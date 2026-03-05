# Workstream 3 - Intelligence Layer (Agent Bricks)

## Status: Foundation Complete, Ready for Agent Development

## Overview

AI-powered diagnostics system using Agent Bricks with vector search over technical manuals to generate smart work orders.

## Architecture

```
Critical Alerts (from DLT Pipeline)
    ↓
Agent Bricks (Claude)
    ├── Tool: get_critical_alerts()
    ├── Tool: retrieve_repair_procedure() → Vector Search
    ├── Tool: get_safety_checklist()
    └── Tool: create_work_order() → Lakebase
```

## Components Completed

### PDF Chunking Pipeline (chunk_pdfs_and_embed.py)
- Extracts text from technical manuals in Unity Catalog volumes
- Chunks into 512-token segments with 50-token overlap
- Metadata: manual_name, asset_type, page_number, section_title
- Schema: `mce_agents.manual_chunks` table created

### Next: Create Vector Search Index

```python
from databricks.vector_search.client import VectorSearchClient

vsc = VectorSearchClient()

# Create endpoint
vsc.create_endpoint(
    name="mce_vector_search_endpoint",
    endpoint_type="STANDARD"
)

# Create index with delta sync
vsc.create_delta_sync_index(
    endpoint_name="mce_vector_search_endpoint",
    source_table_name=f"{CATALOG}.{SCHEMA}.manual_chunks",
    index_name=f"{CATALOG}.{SCHEMA}.manual_index",
    primary_key="chunk_id",
    embedding_source_column="chunk_text",
    embedding_model_endpoint_name="databricks-gte-large-en"
)
```

## Agent Bricks Tools

### Tool 1: get_critical_alerts(site: Optional[str] = None)
```python
def get_critical_alerts(site: str = None):
    """
    Query critical_alerts table from DLT pipeline.
    Returns: List of critical assets with vibration, temp, and maintenance data.
    """
    query = f"""
    SELECT
        asset_id,
        asset_name,
        site,
        asset_type,
        model,
        vibration_hz,
        temp_celsius,
        hours_since_last_maintenance,
        assigned_technician,
        manual_version,
        predicted_failure_type
    FROM {CATALOG}.mce_silver.critical_alerts
    """

    if site:
        query += f" WHERE site = '{site}'"

    query += " ORDER BY vibration_hz DESC"

    # Execute and return results
```

### Tool 2: retrieve_repair_procedure(asset_id: str, failure_type: str)
```python
def retrieve_repair_procedure(asset_id: str, failure_type: str):
    """
    Vector search against manual_index to find relevant repair procedures.

    Args:
        asset_id: Asset requiring repair
        failure_type: BEARING_FAILURE | COOLING_FAULT | GENERAL_ANOMALY

    Returns:
        - procedure_steps: List of repair steps
        - required_parts: List of part numbers and descriptions
        - estimated_duration_hours: Time estimate
    """

    # Get asset type
    asset_info = get_asset_info(asset_id)

    # Build search query
    search_query = f"{failure_type} {asset_info['asset_type']} repair procedure"

    # Vector search
    results = vsc.get_index(f"{CATALOG}.{SCHEMA}.manual_index").similarity_search(
        query_text=search_query,
        columns=["chunk_text", "manual_name", "page_number", "section_title"],
        filters={"asset_type": asset_info['asset_type']},
        num_results=3
    )

    # Extract repair steps and parts from top chunks
    # Parse structured data from manual text
```

### Tool 3: get_safety_checklist(asset_type: str, procedure_type: str)
```python
def get_safety_checklist(asset_type: str, procedure_type: str):
    """
    Retrieve mandatory safety checklist for procedure.

    Returns:
        - mandatory_ppe: List of required personal protective equipment
        - arc_flash_category: Category rating (if applicable)
        - checklist_items: Step-by-step safety checks
        - emergency_contacts: Relevant emergency numbers
    """

    query = f"""
    SELECT
        mandatory_ppe,
        arc_flash_category,
        checklist_items,
        emergency_procedures
    FROM {CATALOG}.mce_silver.safety_checklists
    WHERE asset_type = '{asset_type}'
      AND procedure_type = '{procedure_type}'
    """

    # Return safety checklist
```

### Tool 4: create_work_order(asset_id, procedure, parts, safety, technician_id)
```python
def create_work_order(
    asset_id: str,
    procedure_steps: list,
    required_parts: list,
    safety_checklist: dict,
    technician_id: str
):
    """
    Create work order in Lakebase (Workstream 4 integration).

    Inserts into mce_work_orders table with:
    - Priority: P1 (CRITICAL), P2 (WARNING), P3 (ROUTINE)
    - Status: DISPATCHED
    - AI repair summary
    - Predicted failure date (based on trend analysis)
    """

    work_order = {
        "asset_id": asset_id,
        "priority": "P1",  # CRITICAL
        "status": "DISPATCHED",
        "assigned_technician": technician_id,
        "procedure_steps": json.dumps(procedure_steps),
        "required_parts": json.dumps(required_parts),
        "safety_checklist": json.dumps(safety_checklist),
        "ai_repair_summary": generate_summary(),
        "predicted_failure_date": calculate_failure_date(),
        "created_at": datetime.now()
    }

    # INSERT into Lakebase
    return work_order_id
```

## Agent System Prompt

```
You are the maintenance diagnostics agent for Main Character Energy, an Australian energy company managing 100 critical assets (wind turbines, gas turbines, solar inverters, hydro units, substations) across NSW and VIC.

Your role:
1. Monitor critical alerts from the telemetry system
2. Diagnose failure modes based on sensor patterns
3. Retrieve repair procedures from technical manuals using vector search
4. Generate detailed work orders with:
   - Step-by-step repair procedure
   - Required parts list with SKUs
   - Mandatory safety checklist (ALWAYS included - non-negotiable)
   - Estimated duration
   - Assigned technician

Rules:
- ALWAYS include safety checklist in every work order
- For substations: Include arc flash category and PPE requirements
- For gas turbines: Include temperature thresholds and shutdown procedures
- For wind turbines: Include rotor lock and LOTO procedures
- Prioritize work orders: P1 (CRITICAL > 80Hz), P2 (WARNING 60-80Hz), P3 (ROUTINE)
- Be concise and field-worker-friendly - no jargon

Tone: Professional, direct, safety-focused
```

## Agent Reasoning Chain

```
1. STARTUP: Call get_critical_alerts() → Get list of CRITICAL assets
2. FOR EACH critical asset:
   a. Analyze sensor pattern:
      - High vibration (>80Hz) → BEARING_FAILURE
      - High temperature (>450°C gas, >70°C wind) → COOLING_FAULT
   b. Call retrieve_repair_procedure(asset_id, failure_type)
      - Returns: procedure steps, parts list, duration
   c. Call get_safety_checklist(asset_type, procedure_type)
      - Returns: PPE, arc flash rating, safety checks
   d. Call create_work_order(asset_id, procedure, parts, safety, technician)
      - Inserts work order into Lakebase
3. SUMMARY: Return work orders dispatched count and list
```

## Deployment

### Prerequisites
- Workstream 1: Data in volumes
- Workstream 2: DLT pipeline running, critical_alerts table populated
- Databricks GTE embedding model endpoint enabled

### Deploy Vector Search
```bash
cd workstream-3-intelligence
source ../.venv/bin/activate
python setup_vector_search.py
```

### Deploy Agent
```bash
databricks bundle deploy --profile fe-vm
databricks bundle run agent_endpoint --profile fe-vm
```

### Test Agent
```bash
curl -X POST https://fe-sandbox-serverless-sandbox-tladem.cloud.databricks.com/serving-endpoints/mce_agent/invocations \
  -H "Authorization: Bearer $DATABRICKS_TOKEN" \
  -d '{"messages": [{"role": "user", "content": "Check critical assets and generate work orders"}]}'
```

## Expected Output

```json
{
  "work_orders_dispatched": 8,
  "summary": [
    {
      "work_order_id": "WO-001",
      "asset_id": "MCE-0023",
      "asset_name": "Wind Turbine 23",
      "site": "Sydney North Wind Farm, NSW",
      "priority": "P1",
      "failure_type": "BEARING_FAILURE",
      "required_parts": [
        "SKF-7320-BECBM Main Shaft Bearing Kit",
        "GREASE-EP2-5KG Lithium EP2 Grease Cartridge x3"
      ],
      "safety_checklist": [
        "De-energize turbine and lock out main breaker",
        "Apply rotor lock",
        "Wear fall protection harness"
      ],
      "estimated_duration": "6-8 hours",
      "assigned_technician": "James Chen"
    }
  ]
}
```

## Files

```
workstream-3-intelligence/
├── README.md (this file)
├── chunk_pdfs_and_embed.py       # PDF processing script
├── setup_vector_search.py        # Vector index creation (to be created)
├── agent_tools.py                # Agent Bricks tools (to be created)
├── agent_config.yaml             # Agent configuration (to be created)
└── test_agent.py                 # Agent testing script (to be created)
```

## Next Steps

1. Run `chunk_pdfs_and_embed.py` to create manual_chunks table
2. Create vector search endpoint and index
3. Implement Agent Bricks tools in `agent_tools.py`
4. Deploy agent endpoint
5. Test with critical alerts from Workstream 2
6. Integrate with Lakebase (Workstream 4) for work order storage

## Integration with Workstream 4

Agent creates work orders that will be stored in Lakebase:
- Table: `mce_work_orders`
- Real-time sync to mobile app (Workstream 5)
- Field workers see AI-generated work orders with procedures and safety checklists
