# Main Character Energy
## Agentic Field Management — Claude Code Implementation Plan

---

## Project Structure

```
main-character-energy/
├── workstream-1-foundation/      # Catalog, schemas, mock data
├── workstream-2-ingestion/       # Lakeflow DLT pipelines
├── workstream-3-intelligence/    # Anomaly detection + agent
├── workstream-4-lakebase/        # Live state + work orders
├── workstream-5-app/             # Databricks App (React UI)
└── shared/                       # Config, secrets, utils
```

---

## Workstream 1 — Foundation & Mock Data

**Goal:** Stand up the Unity Catalog structure and seed all mock data before any other workstream can begin. This is the critical path dependency.

### Ralph Wiggum Loop 1-A: Catalog Bootstrap
```
PROMPT → Claude Code generates catalog DDL
  → Run in workspace
  → Validate volumes exist
  → LOOP: fix permissions/grants until clean
```

**Claude Code Prompts:**

```
# Prompt 1-A-1: Catalog scaffold
"Create a Python script using Databricks SDK to provision the following in Unity Catalog:
- Catalog: field_operations_mce
- Schemas: raw, silver, gold, agents, lakebase_sync
- Volumes: /telemetry_ingest, /technical_manuals, /safety_checklists
- Grant READ to group: field_engineers, WRITE to group: pipeline_service
Output the full DDL + SDK calls. Target workspace: [workspace_url]"

# Prompt 1-A-2: Mock data generator
"Write a Python script to generate mock datasets for Main Character Energy, an Australian
energy company. Generate:
1. sensor_telemetry.csv — 100 assets (wind turbines, gas turbines, substations, solar inverters,
   hydro units) across NSW/VIC sites. Columns: asset_id, asset_name, site, asset_type, 
   timestamp, vibration_hz, temp_celsius, rpm, voltage_output. Make 8 assets show 
   CRITICAL vibration (>80Hz) and 5 show WARNING (60-80Hz).
2. asset_registry.json — master asset list with serial_number, model, install_date, 
   warranty_expiry, manual_version, assigned_technician.
3. maintenance_history.parquet — 3 years of maintenance events per asset.
Upload all three to Volume: field_operations_mce.raw.telemetry_ingest"

# Prompt 1-A-3: Mock PDF manuals
"Generate a Python script using reportlab to create 3 mock technical repair manuals as PDFs:
1. vestas_v150_repair_manual.pdf — wind turbine, include vibration bearing replacement procedure,
   parts list (bearing kit SKF-7320, torque wrench set, grease cartridge x3)
2. ge_7ha_gas_turbine_manual.pdf — gas turbine, compressor blade inspection procedure
3. abb_substation_manual.pdf — switchgear maintenance, arc flash safety checklist
Store in Volume: field_operations_mce.raw.technical_manuals"
```

### Ralph Wiggum Loop 1-B: Schema Validation
```
PROMPT → Generate Delta table schemas from CSV/JSON
  → Run CREATE TABLE AS SELECT
  → Profile with dbutils.data.summarize()
  → LOOP: if nulls/type mismatches found → regenerate mock data with fixes
  → EXIT when all tables pass data quality checks
```

---

## Workstream 2 — Lakeflow Ingestion Pipelines

**Goal:** Build Spark Declarative Pipelines that continuously ingest telemetry into Silver Delta tables with real-time anomaly thresholds applied.

### Ralph Wiggum Loop 2-A: DLT Pipeline Build
```
PROMPT → Generate pipeline YAML + Python
  → Deploy via Databricks CLI
  → Trigger full refresh
  → LOOP: inspect event log for schema evolution errors
  → LOOP: tune watermark/trigger intervals until latency < 30s
  → EXIT when Critical_Alerts table populating correctly
```

**Claude Code Prompts:**

```
# Prompt 2-A-1: Bronze ingestion pipeline
"Write a Lakeflow Spark Declarative Pipeline (Python DLT) for Main Character Energy that:
- Reads new files from Volume path: /Volumes/field_operations_mce/raw/telemetry_ingest/
- Creates a Bronze streaming table: bronze_telemetry with schema enforcement
- Adds ingestion metadata: _ingest_timestamp, _source_file, _pipeline_run_id
- Applies expectations: CONSTRAINT valid_vibration EXPECT vibration_hz BETWEEN 0 AND 500"

# Prompt 2-A-2: Silver anomaly detection pipeline
"Extend the DLT pipeline to create a Silver layer for Main Character Energy:
- silver_asset_telemetry: cleaned, deduplicated, joined with asset_registry on asset_id
- critical_alerts: filtered view where vibration_hz > 80 OR temp_celsius > 450
  Add columns: alert_severity (CRITICAL/WARNING), alert_timestamp, hours_since_last_maintenance
- Apply SCD Type 1 APPLY CHANGES INTO for asset current state tracking
Use @dlt.expect_all_or_drop for data quality."

# Prompt 2-A-3: Safety checklist pipeline
"Build a DLT pipeline that reads safety_checklists/ Volume (JSON files) and creates:
- silver_safety_checklists table with columns: checklist_id, asset_type, procedure_type,
  checklist_items (array<struct>), mandatory_ppe, arc_flash_category, approved_by, version
This will be used by the agent to append safety items to every work order."
```

### Ralph Wiggum Loop 2-B: Continuous Quality Gate
```
Every pipeline run →
  → Check: critical_alerts row count > 0?
  → Check: asset_registry join hit rate > 95%?
  → NO → re-examine mock data, patch generator, re-upload
  → YES → proceed to Workstream 3
```

---

## Workstream 3 — Intelligence Layer (Anomaly Agent)

**Goal:** Build the Agent Bricks agent that reasons over flagged assets, retrieves repair procedures via vector search, and produces Smart Work Orders with safety compliance appended.

### Ralph Wiggum Loop 3-A: Vector Search Index Build
```
PROMPT → Chunk PDF manuals → embed → index
  → Test similarity queries
  → LOOP: adjust chunk size (256 → 512 → 1024 tokens)
  → LOOP: test retrieval precision with known procedure queries
  → EXIT when top-1 retrieval matches correct manual for asset type
```

**Claude Code Prompts:**

```
# Prompt 3-A-1: PDF chunking + embedding
"Write a Python script using LangChain + Databricks Vector Search to:
1. Load all PDFs from Volume: field_operations_mce.raw.technical_manuals
2. Chunk each PDF into 512-token segments with 50-token overlap
3. Embed using databricks-gte-large-en endpoint
4. Create a Vector Search index: field_operations_mce.agents.manual_index
   with delta sync on table: field_operations_mce.agents.manual_chunks
Include metadata per chunk: manual_name, asset_type, section_title, page_number"

# Prompt 3-A-2: Agent tools definition
"Using Agent Bricks (Mosaic AI Agent Framework), define the following tools for the 
Main Character Energy maintenance agent:

Tool 1 — get_critical_alerts(site: str = None)
  Query field_operations_mce.silver.critical_alerts, return asset_id, alert_severity,
  vibration_hz, temp_celsius, hours_since_last_maintenance

Tool 2 — retrieve_repair_procedure(asset_id: str, failure_type: str)
  Vector search query against manual_index, top-3 chunks, filter by asset_type
  Return: procedure_steps (list), required_parts (list), estimated_duration_hours

Tool 3 — get_safety_checklist(asset_type: str, procedure_type: str)
  Query silver_safety_checklists, return mandatory_ppe, arc_flash_category, checklist_items

Tool 4 — create_work_order(asset_id, procedure, parts, safety_items, technician_id)
  INSERT into Lakebase table: mce_work_orders (Workstream 4)
  Return: work_order_id"

# Prompt 3-A-3: Agent system prompt + reasoning chain
"Write the system prompt and Claude reasoning chain for the Main Character Energy 
field maintenance agent. The agent should:
1. Call get_critical_alerts() on startup
2. For each critical asset, call retrieve_repair_procedure() to diagnose likely failure mode
   based on sensor pattern (high vibration = bearing failure, high temp = cooling fault)
3. Call get_safety_checklist() and ALWAYS append to every work order — non-negotiable
4. Call create_work_order() with full pre-diagnosed Smart Work Order
5. Return a summary of work orders dispatched

Tone: professional, concise, field-worker-friendly. No jargon.
Output format per work order: asset, site, priority, ETA, required_parts[], safety_checklist[]"
```

### Ralph Wiggum Loop 3-B: Agent Hallucination Check
```
PROMPT → Run agent against all 8 CRITICAL assets
  → For each work order output:
    → LOOP: does parts_list reference real part numbers from manual? 
    → LOOP: does safety_checklist match asset_type?
    → LOOP: is procedure_steps non-empty?
  → If any check fails → refine tool definitions or system prompt
  → EXIT when all 8 work orders pass validation
```

---

## Workstream 4 — Lakebase Live State

**Goal:** Provision the Serverless Postgres (Lakebase) tables that the agent writes to and the mobile app reads from in real-time.

### Ralph Wiggum Loop 4-A: Schema + Connection
```
PROMPT → Generate Lakebase DDL
  → Test psycopg2 connection from Databricks notebook
  → LOOP: fix connection string / secret scope issues
  → Run INSERT test → SELECT test
  → EXIT when round-trip latency < 100ms
```

**Claude Code Prompts:**

```
# Prompt 4-A-1: Lakebase DDL
"Create the Lakebase (Serverless Postgres) DDL for Main Character Energy with tables:

1. mce_assets_live_status
   - asset_id PK, site, asset_type, vibration_hz, temp_celsius, status (CRITICAL/WARNING/HEALTHY),
     last_updated TIMESTAMPTZ, active_work_order_id

2. mce_work_orders
   - work_order_id UUID PK DEFAULT gen_random_uuid(), asset_id FK, created_at TIMESTAMPTZ,
     priority (P1/P2/P3), status (DISPATCHED/IN_PROGRESS/COMPLETE/CANCELLED),
     assigned_technician, predicted_failure_date DATE, required_parts JSONB,
     procedure_steps JSONB, safety_checklist JSONB, ai_repair_summary TEXT,
     first_time_fix_verified BOOLEAN DEFAULT FALSE

3. mce_technicians
   - technician_id PK, name, site, certifications JSONB, current_location TEXT, available BOOLEAN

Include indexes on asset_id, status, priority. Add updated_at trigger."

# Prompt 4-A-2: Sync pipeline (Delta → Lakebase)
"Write a Python function using Databricks Connect + psycopg2 that:
- Reads new rows from field_operations_mce.silver.critical_alerts (using Delta change data feed)
- UPSERTs into Lakebase mce_assets_live_status using ON CONFLICT DO UPDATE
- Runs on a 30-second micro-batch trigger
Store Lakebase credentials in Databricks Secret Scope: mce-secrets / lakebase-conn-string"
```

### Ralph Wiggum Loop 4-B: Concurrency Stress Test
```
PROMPT → Simulate 50 concurrent mobile reads + 10 agent writes
  → Measure p95 latency
  → LOOP: if p95 > 500ms → add connection pooling (PgBouncer config)
  → EXIT when stable under load
```

---

## Workstream 5 — Databricks App (Mobile Field UI)

**Goal:** A mobile-responsive Databricks App where field workers see agent-dispatched tasks, safety checklists, and can update work order status in real-time.

### Ralph Wiggum Loop 5-A: App Scaffold + Auth
```
PROMPT → Scaffold React app with Databricks App auth
  → Deploy to Databricks Apps
  → LOOP: fix OAuth / service principal scoping
  → Test with field_engineers group user
  → EXIT when login works for non-admin user
```

**Claude Code Prompts:**

```
# Prompt 5-A-1: App backend (FastAPI)
"Write a FastAPI backend for the Main Character Energy Field Management App:

Endpoints:
GET  /api/assets          — query Lakebase mce_assets_live_status, filter by site/status
GET  /api/workorders      — fetch open work orders for technician_id, include parts + checklist
POST /api/workorders/{id}/status — update status (IN_PROGRESS / COMPLETE)
POST /api/workorders/{id}/ftf    — mark first_time_fix_verified = true
GET  /api/agent/dispatch  — trigger the Agent Bricks endpoint to scan for new criticals and 
                            generate work orders
GET  /health              — liveness probe

Auth: Databricks OAuth (bearer token forwarded from frontend)
DB: psycopg2 connection pool (min=2, max=10) to Lakebase using secret scope mce-secrets"

# Prompt 5-A-2: React frontend
"Build a mobile-responsive React app for Main Character Energy field workers.
Design: dark industrial theme, amber/orange accent colors (#F59E0B), card-based layout.

Views:
1. Dashboard — KPI cards: Active Criticals, Dispatched Work Orders, Avg First-Time Fix Rate
   Asset status heatmap grid (color-coded CRITICAL=red, WARNING=amber, HEALTHY=green)
   'Run Agent Dispatch' button that calls /api/agent/dispatch

2. Work Orders List — sorted by priority (P1 first), shows asset name, site, ETA
   Filter tabs: All / My Tasks / By Site

3. Work Order Detail — full AI repair summary, expandable step-by-step procedure,
   required parts checklist (tap to check off), safety checklist (MANDATORY, highlighted),
   status update buttons: [Start Job] [Complete] [Escalate]

4. Asset Map — simple site cards showing asset count per site with status badges

Use Tailwind CSS. Poll /api/assets every 30s for live updates."

# Prompt 5-A-3: Databricks App config
"Write the app.yaml and requirements.txt for deploying this as a Databricks App.
Configure: 
- compute: serverless
- env vars sourced from secret scope mce-secrets
- entrypoint: uvicorn main:app
- static_files: ./frontend/dist
Include a deploy.sh script using Databricks CLI v2."
```

### Ralph Wiggum Loop 5-B: End-to-End Smoke Test
```
Full loop test:
  1. Upload new telemetry CSV with 2 new CRITICAL assets → Volume
  2. DLT pipeline picks up → silver_critical_alerts updated
  3. Delta→Lakebase sync fires → mce_assets_live_status updated
  4. App dashboard shows new criticals within 30s
  5. Click 'Run Agent Dispatch' → agent creates 2 work orders in Lakebase
  6. Work orders appear in field worker's list
  7. Field worker marks P1 complete + checks FTF = true
  8. Dashboard KPIs update

LOOP: repeat until all 8 steps pass without manual intervention
```

---

## Cross-Workstream Ralph Wiggum Loop — Integration Hell Buster

```
After WS 1-4 individually pass:

LOOP (run daily during build):
  → Re-run mock data generator with new random seed
  → Full pipeline refresh
  → Agent dispatch end-to-end
  → Assert: work_order count == critical_asset count
  → Assert: every work order has safety_checklist.length > 0
  → Assert: required_parts references valid SKUs from manuals
  → Assert: Lakebase latency p95 < 200ms
  → Assert: App loads in < 3s on mobile viewport
  
If ANY assertion fails → identify workstream owner → targeted fix loop
EXIT when 3 consecutive clean runs achieved
```

---

## Claude Code Session Kickoff Prompt

Paste this at the start of every Claude Code session:

```
You are the lead engineer for Main Character Energy's Agentic Field Management platform,
built on Databricks. The stack is:
- Unity Catalog: field_operations_mce (schemas: raw, silver, gold, agents)
- Lakeflow DLT: Python declarative pipelines, streaming from Volumes
- Lakebase: Serverless Postgres for live asset state + work orders
- Agent Bricks: tool-calling agent with vector search over PDF manuals
- Databricks App: FastAPI backend + React frontend, mobile-first

Current workstream: [PASTE WORKSTREAM NAME]
Current task: [PASTE SPECIFIC PROMPT]

Rules:
1. Always use Secret Scope 'mce-secrets' for credentials — never hardcode
2. Every work order MUST include a safety checklist — enforce in agent tool
3. Lakebase is the source of truth for live state — not Delta tables
4. All Unity Catalog objects prefixed: field_operations_mce.<schema>.<table>
5. Target Python 3.11, Databricks Runtime 15.4 LTS ML
```
