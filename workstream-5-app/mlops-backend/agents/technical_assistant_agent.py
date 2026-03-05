"""
Technical Assistant Agent - Agent Bricks Framework Integration
Uses Claude AI to generate intelligent work orders from critical alerts

This agent:
1. Monitors agents_unprocessed_alerts table
2. Retrieves relevant technical manual via vector search
3. Uses Claude to reason about failure type and generate work order
4. Validates against safety checklist
5. Writes work order to Lakebase for mobile app
"""

import anthropic
import os
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.vectorsearch import VectorSearchIndex
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import json

# Initialize clients
w = WorkspaceClient()
claude_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Lakebase connection
LAKEBASE_CONN_STRING = os.environ.get("LAKEBASE_CONN_STRING")

# Safety checklists by asset type
SAFETY_CHECKLISTS = {
    "wind_turbine": [
        "Engage lockout/tagout before entering nacelle",
        "Wear fall protection harness at all times",
        "Check wind speed < 15 m/s before starting work",
        "Minimum crew size: 2 technicians",
        "Emergency descent equipment verified"
    ],
    "solar_inverter": [
        "De-energize DC input before accessing internals",
        "Verify zero voltage with multimeter",
        "Wear arc flash rated PPE (40 cal/cm²)",
        "Use insulated tools only",
        "Maintain 1m clearance around equipment"
    ],
    "gas_turbine": [
        "Verify 24-hour cooldown period completed",
        "Hot gas path temperature < 100°C verified",
        "High-temperature PPE required (rating: 600°C)",
        "Gas detection equipment operational",
        "Emergency shutdown procedures reviewed"
    ],
    "hydro_unit": [
        "Water intake gates closed and locked",
        "Turbine fully drained",
        "Confined space entry permit obtained",
        "Atmospheric testing completed",
        "Rescue equipment stationed topside"
    ],
    "substation": [
        "High voltage isolation verified",
        "Earth switches closed",
        "Safety tags and locks applied",
        "Arc flash boundary established",
        "Rubber insulating equipment inspected"
    ]
}

# Technical manual content (in production, this would be in Vector Search)
TECHNICAL_MANUALS = {
    "wind_turbine": {
        "bearing_failure": {
            "required_parts": "SKF 7320 BECBM main bearing kit, High-temperature bearing grease (5kg), Hydraulic puller set",
            "procedure_steps": [
                "Engage lockout/tagout and verify wind speed < 15 m/s",
                "Access nacelle with fall protection",
                "Drain gearbox oil and inspect for metal shavings",
                "Remove nacelle cover panels",
                "Use hydraulic puller to extract damaged bearing",
                "Clean bearing housing thoroughly",
                "Install new bearing with proper alignment (tolerance: 0.05mm)",
                "Apply high-temp grease per manufacturer spec",
                "Reassemble and perform vibration test",
                "Document bearing serial number and installation torque values"
            ],
            "estimated_hours": 8,
            "failure_indicators": "High vibration (>80Hz), metal shavings in oil, unusual noise"
        },
        "gearbox_wear": {
            "required_parts": "Gearbox overhaul kit, Mobil SHC 634 synthetic oil (200L)",
            "procedure_steps": [
                "Lockout turbine and access nacelle",
                "Drain gearbox oil and collect sample for analysis",
                "Remove gearbox inspection covers",
                "Inspect gear teeth for pitting and spalling",
                "Replace worn gears if tooth wear > 15%",
                "Flush gearbox with cleaning solution",
                "Fill with new synthetic oil",
                "Run low-speed test (< 50% rated RPM)",
                "Monitor vibration and oil temperature"
            ],
            "estimated_hours": 12,
            "failure_indicators": "Vibration 65-80Hz, oil contamination, temperature rise"
        }
    },
    "solar_inverter": {
        "inverter_overheating": {
            "required_parts": "ABB cooling fan assembly (PVS800-FAN-02), Fan controller board, Thermal paste",
            "procedure_steps": [
                "De-energize DC input and verify zero voltage",
                "Remove inverter side panels (PPE required)",
                "Inspect cooling fans - check for bearing wear",
                "Remove failed fan assembly (4x M6 bolts)",
                "Clean heat sink fins with compressed air",
                "Apply new thermal paste to heat sink interface",
                "Install new fan assembly",
                "Reconnect fan controller",
                "Power up and verify fan operation",
                "Monitor temperature during 1-hour test run"
            ],
            "estimated_hours": 4,
            "failure_indicators": "Temperature >70°C, fan not spinning, thermal shutdown events"
        }
    },
    "gas_turbine": {
        "compressor_blade": {
            "required_parts": "Stage 1-3 compressor blade set (7HA-CB-S123), Blade root locking pins, Anti-seize compound",
            "procedure_steps": [
                "Verify 24-hour cooldown completed",
                "Perform borescope inspection of all compressor stages",
                "Document blade damage location and extent",
                "Remove turbine casing (12x M24 bolts)",
                "Extract damaged blades using specialized tooling",
                "Inspect blade dovetails for cracking (dye penetrant test)",
                "Install new blades with anti-seize on roots",
                "Verify blade tip clearance (spec: 0.5-0.8mm)",
                "Reassemble casing with new gaskets",
                "Perform low-speed balance check"
            ],
            "estimated_hours": 16,
            "failure_indicators": "High vibration (>80Hz), compressor surge, efficiency drop"
        }
    }
}

def retrieve_technical_manual(asset_type: str, vibration_hz: float, temp_celsius: float) -> dict:
    """
    Retrieve relevant technical manual section based on symptoms
    In production, this would use Databricks Vector Search
    """

    # Simple heuristic for demo (replace with vector search)
    if asset_type == "wind_turbine":
        if vibration_hz > 80:
            return TECHNICAL_MANUALS["wind_turbine"]["bearing_failure"]
        else:
            return TECHNICAL_MANUALS["wind_turbine"]["gearbox_wear"]

    elif asset_type == "solar_inverter":
        if temp_celsius > 70:
            return TECHNICAL_MANUALS["solar_inverter"]["inverter_overheating"]

    elif asset_type == "gas_turbine":
        if vibration_hz > 80:
            return TECHNICAL_MANUALS["gas_turbine"]["compressor_blade"]

    # Default fallback
    return {
        "required_parts": "Standard maintenance kit",
        "procedure_steps": ["Inspect equipment", "Identify fault", "Replace failed component", "Test operation"],
        "estimated_hours": 6,
        "failure_indicators": "Abnormal sensor readings"
    }

def generate_work_order_with_claude(alert: dict, technical_manual: dict) -> dict:
    """
    Use Claude to generate an intelligent work order with AI reasoning
    """

    system_prompt = """You are an expert field service engineer for Main Character Energy.
    You analyze equipment failures and generate detailed work orders for field technicians.

    Your work orders must include:
    1. Clear diagnosis of the failure based on sensor data
    2. Required parts list (specific part numbers)
    3. Step-by-step repair procedure
    4. Estimated duration
    5. AI repair summary explaining the reasoning

    Be precise, safety-focused, and include all details a field technician needs."""

    user_prompt = f"""Generate a work order for this critical alert:

Asset: {alert['asset_name']} (ID: {alert['asset_id']})
Type: {alert['asset_type']}
Location: {alert['site']}
Alert: {alert['alert_description']}

Current Sensor Readings:
- Vibration: {alert['vibration_hz']} Hz (CRITICAL - threshold exceeded)
- Temperature: {alert['temp_celsius']}°C
- Alert Time: {alert['alert_timestamp']}

Technical Manual Reference:
Required Parts: {technical_manual['required_parts']}
Procedure Steps:
{chr(10).join(f'{i+1}. {step}' for i, step in enumerate(technical_manual['procedure_steps']))}
Estimated Duration: {technical_manual['estimated_hours']} hours
Failure Indicators: {technical_manual['failure_indicators']}

Based on this information, provide:
1. A diagnostic summary (2-3 sentences explaining WHY this failure occurred)
2. The specific failure type (e.g., "Bearing failure", "Inverter overheating")
3. Predicted failure date (estimate based on vibration severity)
4. Priority level (P1 if vibration > 90Hz, P2 if > 80Hz, P3 otherwise)

Format your response as JSON:
{{
  "failure_type": "...",
  "predicted_failure_date": "YYYY-MM-DD",
  "priority": "P1|P2|P3",
  "ai_repair_summary": "Your 2-3 sentence diagnostic reasoning here",
  "required_parts": "Exact parts needed",
  "procedure_steps": "Full repair procedure as multi-line string",
  "estimated_duration_hours": 8
}}"""

    try:
        response = claude_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        # Parse Claude's response
        response_text = response.content[0].text

        # Extract JSON from response (Claude might wrap it in markdown)
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        work_order_data = json.loads(response_text)

        return work_order_data

    except Exception as e:
        print(f"Error calling Claude API: {e}")
        # Fallback to basic work order
        return {
            "failure_type": "Unknown - Manual inspection required",
            "predicted_failure_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
            "priority": "P2",
            "ai_repair_summary": f"Asset {alert['asset_id']} showing critical vibration levels. Manual inspection recommended.",
            "required_parts": technical_manual['required_parts'],
            "procedure_steps": "\n".join(technical_manual['procedure_steps']),
            "estimated_duration_hours": technical_manual['estimated_hours']
        }

def validate_safety_checklist(asset_type: str) -> str:
    """
    Get mandatory safety checklist for asset type
    """
    return "\n".join(f"☐ {item}" for item in SAFETY_CHECKLISTS.get(asset_type, []))

def assign_technician(asset_type: str, site: str) -> str:
    """
    Assign appropriate technician based on certification and location
    In production, this would query Lakebase for available technicians
    """
    # Simple assignment logic (replace with database query)
    technicians = {
        "wind_turbine": "James Chen",
        "solar_inverter": "David Martinez",
        "gas_turbine": "Michael O'Donnell",
        "hydro_unit": "Emma Thompson",
        "substation": "Lisa Anderson"
    }
    return technicians.get(asset_type, "Unassigned - Contact dispatch")

def create_work_order_in_lakebase(alert: dict, work_order_data: dict, safety_checklist: str, technician: str):
    """
    Write the AI-generated work order to Lakebase
    This makes it immediately available in the mobile app
    """

    try:
        conn = psycopg2.connect(LAKEBASE_CONN_STRING)
        cursor = conn.cursor()

        # Generate work order ID
        work_order_id = f"WO-{datetime.now().strftime('%Y%m%d')}-{alert['asset_id'].split('-')[1]}"

        insert_query = """
        INSERT INTO mce_operations.mce_work_orders (
            work_order_id, asset_id, created_at, priority, status,
            assigned_technician, predicted_failure_date, predicted_failure_type,
            required_parts, procedure_steps, safety_checklist,
            ai_repair_summary, estimated_duration_hours, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (work_order_id) DO NOTHING;
        """

        cursor.execute(insert_query, (
            work_order_id,
            alert['asset_id'],
            datetime.now(),
            work_order_data['priority'],
            'DISPATCHED',
            technician,
            work_order_data['predicted_failure_date'],
            work_order_data['failure_type'],
            work_order_data['required_parts'],
            work_order_data['procedure_steps'],
            safety_checklist,
            work_order_data['ai_repair_summary'],
            work_order_data['estimated_duration_hours'],
            datetime.now()
        ))

        conn.commit()
        cursor.close()
        conn.close()

        print(f"✓ Work order {work_order_id} created in Lakebase")
        return work_order_id

    except Exception as e:
        print(f"Error writing to Lakebase: {e}")
        return None

def process_unprocessed_alerts():
    """
    Main agent loop: Monitor for unprocessed alerts and generate work orders
    """

    print("=" * 80)
    print("TECHNICAL ASSISTANT AGENT - STARTED")
    print("=" * 80)

    # In production, this would query the Delta table via Databricks SQL
    # For now, we'll simulate with Lakebase query

    try:
        conn = psycopg2.connect(LAKEBASE_CONN_STRING)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get critical assets without work orders
        cursor.execute("""
            SELECT DISTINCT asset_id, asset_name, asset_type, site,
                   vibration_hz, temp_celsius, status
            FROM mce_operations.mce_assets_live_status
            WHERE status = 'CRITICAL'
              AND asset_id NOT IN (
                  SELECT asset_id FROM mce_operations.mce_work_orders
                  WHERE status IN ('DISPATCHED', 'IN_PROGRESS')
              )
            LIMIT 10;
        """)

        unprocessed_alerts = cursor.fetchall()
        cursor.close()
        conn.close()

        print(f"\nFound {len(unprocessed_alerts)} unprocessed critical alerts")

        for alert in unprocessed_alerts:
            print(f"\n[Processing] {alert['asset_id']} - {alert['asset_name']}")

            # Step 1: Retrieve technical manual
            print("  → Retrieving technical manual...")
            technical_manual = retrieve_technical_manual(
                alert['asset_type'],
                alert['vibration_hz'],
                alert['temp_celsius']
            )

            # Step 2: Generate work order with Claude
            print("  → Calling Claude AI for diagnosis...")
            alert_for_claude = {
                **dict(alert),
                'alert_description': f"Critical vibration alert: {alert['vibration_hz']} Hz",
                'alert_timestamp': datetime.now().isoformat()
            }
            work_order_data = generate_work_order_with_claude(alert_for_claude, technical_manual)

            # Step 3: Validate safety checklist
            print("  → Validating safety requirements...")
            safety_checklist = validate_safety_checklist(alert['asset_type'])

            # Step 4: Assign technician
            print("  → Assigning technician...")
            technician = assign_technician(alert['asset_type'], alert['site'])

            # Step 5: Create work order in Lakebase
            print("  → Creating work order in Lakebase...")
            work_order_id = create_work_order_in_lakebase(
                alert_for_claude,
                work_order_data,
                safety_checklist,
                technician
            )

            if work_order_id:
                print(f"  ✓ Work order {work_order_id} created successfully")
                print(f"    Priority: {work_order_data['priority']}")
                print(f"    Technician: {technician}")
                print(f"    Estimated: {work_order_data['estimated_duration_hours']} hours")
            else:
                print(f"  ✗ Failed to create work order")

        print("\n" + "=" * 80)
        print(f"AGENT RUN COMPLETE - Processed {len(unprocessed_alerts)} alerts")
        print("=" * 80)

    except Exception as e:
        print(f"Error in agent loop: {e}")

if __name__ == "__main__":
    process_unprocessed_alerts()
