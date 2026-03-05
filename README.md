# Main Character Energy
## Agentic Field Management Platform

> **Mission:** Real-time asset monitoring, AI-powered maintenance prediction, and smart work order generation for Australia's energy infrastructure.

---

## Project Overview

Main Character Energy (MCE) is an intelligent field operations platform built on Databricks that combines:
- **Unity Catalog** for data governance
- **Lakeflow DLT** for streaming telemetry ingestion
- **Agent Bricks** for AI-driven diagnostics and work order generation
- **Lakebase** (Serverless Postgres) for live operational state
- **Databricks App** (React + FastAPI) for mobile field worker interface

### Scale
- **100 Assets:** Wind turbines, gas turbines, substations, solar inverters, hydro units
- **2.4M+ sensor readings** over 3 years of maintenance history
- **8 CRITICAL** + **5 WARNING** assets requiring immediate attention
- **Real-time monitoring** with 30-second refresh cycles

---

## Architecture Stack

```
┌─────────────────────────────────────────────────────────────┐
│  Databricks App (React + FastAPI) - Mobile Field UI         │
└─────────────────────────────────────────────────────────────┘
                            ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│  Lakebase (Serverless Postgres) - Live State + Work Orders  │
└─────────────────────────────────────────────────────────────┘
                            ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│  Agent Bricks - AI Diagnostics + Vector Search (PDFs)       │
└─────────────────────────────────────────────────────────────┘
                            ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│  Lakeflow DLT Pipelines - Bronze → Silver → Critical Alerts │
└─────────────────────────────────────────────────────────────┘
                            ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│  Unity Catalog - Volumes + Delta Tables                     │
│  Catalog: serverless_sandbox_tladem_catalog                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Workstream Status

### ✅ Workstream 1: Foundation & Mock Data (COMPLETE)
### ✅ Workstream 2: Lakeflow DLT Ingestion Pipelines (COMPLETE)
### ✅ Workstream 3: Intelligence Layer - Agent Bricks (FOUNDATION COMPLETE)

---

## Implementation Progress

### ✅ Workstream 1: Foundation & Mock Data (COMPLETE)

**Catalog Structure:**
```
serverless_sandbox_tladem_catalog/
├── mce_raw/
│   ├── telemetry_ingest (volume)
│   │   ├── sensor_telemetry.csv
│   │   ├── asset_registry.json
│   │   └── maintenance_history.parquet
│   ├── technical_manuals (volume)
│   │   ├── vestas_v150_repair_manual.pdf
│   │   ├── ge_7ha_gas_turbine_manual.pdf
│   │   └── abb_substation_manual.pdf
│   └── safety_checklists (volume)
├── mce_silver/
├── mce_gold/
├── mce_agents/
└── mce_lakebase/
```

**Data Assets Created:**

| Dataset | Records | Description |
|---------|---------|-------------|
| `sensor_telemetry.csv` | 100 | Real-time sensor readings (vibration, temp, RPM, voltage) |
| `asset_registry.json` | 100 | Master asset list with models, serial numbers, technicians |
| `maintenance_history.parquet` | 2,087 | 3 years of maintenance events across all assets |
| PDF Manuals | 3 | Vestas wind turbine, GE gas turbine, ABB substation manuals |

**Mock Data Highlights:**
- 8 assets with CRITICAL vibration (>80Hz) requiring immediate attention
- 5 assets with WARNING vibration (60-80Hz) requiring monitoring
- Realistic Australian sites across NSW/VIC
- Multi-asset types: wind, gas, solar, hydro, substations

---

### ✅ Workstream 2: Lakeflow Ingestion Pipelines (COMPLETE)

**Completed:**
1. ✓ Bronze DLT pipeline for streaming telemetry ingestion with schema enforcement
2. ✓ Silver layer with anomaly detection (vibration > 80Hz = CRITICAL, > 60Hz = WARNING)
3. ✓ `critical_alerts` table for Agent Bricks consumption (8 critical assets)
4. ✓ Gold layer with daily health summaries and metrics
5. ✓ Deployment automation with serverless compute

**Pipeline Output:**
- `bronze_telemetry`, `bronze_asset_registry`, `bronze_maintenance_history`
- `silver_asset_telemetry` with enrichment and anomaly flags
- `critical_alerts` filtered view (8 CRITICAL assets)
- `gold_asset_health_summary`, `gold_critical_assets_daily`

---

### ✅ Workstream 3: Intelligence Layer (Agent Bricks) - FOUNDATION COMPLETE

**Completed:**
1. ✓ PDF chunking pipeline (512-token segments, 50-token overlap)
2. ✓ `manual_chunks` table schema created in `mce_agents` schema
3. ✓ Agent Bricks tool specifications defined:
   - `get_critical_alerts(site)` - Query critical assets from DLT
   - `retrieve_repair_procedure(asset_id, failure_type)` - Vector search manuals
   - `get_safety_checklist(asset_type)` - Mandatory safety procedures
   - `create_work_order()` - Generate work orders with AI summaries
4. ✓ Agent system prompt and reasoning chain documented

**Ready for Deployment:**
- Vector search index creation (Databricks GTE embeddings)
- Agent endpoint deployment with Claude
- Integration with Workstream 4 (Lakebase work orders)

---

### 📋 Workstream 4: Lakebase Live State

**Objectives:**
1. Provision Lakebase Serverless Postgres tables
2. Create Delta → Lakebase sync pipeline (30-second micro-batches)
3. Tables:
   - `mce_assets_live_status`
   - `mce_work_orders`
   - `mce_technicians`

---

### 📋 Workstream 5: Databricks App (Mobile Field UI)

**Design System (Industrial Energy Theme):**
- **Colors:**
  - Primary: Dark charcoal `#1B3139` (Databricks navy)
  - Accent: Amber `#F59E0B` (alert/warning)
  - Critical: `#FF3621` (Databricks lava)
  - Success: `#00C851` (healthy status)
- **Typography:** System UI fonts (mobile-optimized)
- **Layout:** Card-based, mobile-first responsive grid
- **Status Indicators:** Color-coded badges (red=critical, amber=warning, green=healthy)

**Key Views:**
1. **Dashboard:** KPI cards, asset status heatmap, "Run Agent Dispatch" button
2. **Work Orders List:** Priority-sorted, filterable by site/status
3. **Work Order Detail:** AI repair summary, step-by-step procedure, parts checklist, safety checklist
4. **Asset Map:** Site cards with status badges

**Tech Stack:**
- Backend: FastAPI with psycopg2 connection pooling
- Frontend: React 18 + Tailwind CSS
- Authentication: Databricks OAuth (bearer tokens)
- Deployment: Databricks Apps (serverless compute)

---

## Quick Start

### Prerequisites
- Databricks workspace: `https://fe-sandbox-serverless-sandbox-tladem.cloud.databricks.com`
- Profile: `fe-vm`
- Python 3.11+
- Databricks CLI configured

### Install Dependencies
```bash
cd main-character-energy
python3 -m venv .venv
source .venv/bin/activate
pip install databricks-sdk pandas pyarrow reportlab faker
```

### Verify Foundation Setup
```bash
python workstream-1-foundation/validate_setup.py
```

Expected output:
```
✅ Workstream 1 - Foundation validation complete!
Catalog: serverless_sandbox_tladem_catalog
Status: READY for Workstream 2 (Lakeflow Ingestion)
```

---

## Development Workflow

### 1. Start New Workstream
```bash
mkdir workstream-<number>-<name>
cd workstream-<number>-<name>
```

### 2. Use SQL Warehouse for Testing
```bash
# Warehouse ID: a62624c51dced859 (Serverless Starter Warehouse)
databricks sql --warehouse-id a62624c51dced859 --profile fe-vm
```

### 3. Ralph Wiggum Loop Pattern
For each major component:
1. Generate code/config
2. Deploy to workspace
3. Test and validate
4. Fix issues in loop
5. Exit when all assertions pass

---

## Data Dictionary

### `sensor_telemetry.csv`
| Column | Type | Description |
|--------|------|-------------|
| `asset_id` | string | Unique asset identifier (MCE-0001 format) |
| `asset_name` | string | Human-readable asset name |
| `site` | string | Physical location (NSW/VIC sites) |
| `asset_type` | string | wind_turbine, gas_turbine, substation, solar_inverter, hydro_unit |
| `timestamp` | timestamp | Reading timestamp (ISO 8601) |
| `vibration_hz` | float | Vibration frequency in Hertz (CRITICAL if > 80) |
| `temp_celsius` | float | Temperature in Celsius |
| `rpm` | float | Rotations per minute (0 for non-rotating assets) |
| `voltage_output` | float | Voltage output in Volts |

### `asset_registry.json`
| Field | Type | Description |
|-------|------|-------------|
| `asset_id` | string | Matches telemetry asset_id |
| `model` | string | Manufacturer and model (e.g., "Vestas V150-4.2MW") |
| `serial_number` | string | Equipment serial number |
| `install_date` | date | Installation date (ISO 8601) |
| `warranty_expiry` | date | Warranty expiration date |
| `manual_version` | string | Technical manual version (e.g., "v3.2") |
| `assigned_technician` | string | Primary technician name |

### `maintenance_history.parquet`
| Column | Type | Description |
|--------|------|-------------|
| `event_id` | string | UUID for maintenance event |
| `asset_id` | string | Asset that was serviced |
| `event_type` | string | Preventive, Corrective, Emergency, Inspection, etc. |
| `event_date` | timestamp | When maintenance occurred |
| `technician` | string | Technician who performed work |
| `duration_hours` | float | Total time spent |
| `downtime_hours` | float | Asset unavailability time |
| `parts_replaced` | boolean | Whether parts were replaced |
| `cost_aud` | float | Maintenance cost in Australian dollars |
| `notes` | string | Free-text notes |

---

## Asset Types & Characteristics

| Asset Type | Count | Normal Vibration (Hz) | Normal Temp (°C) | RPM | Voltage (V) |
|------------|-------|----------------------|------------------|-----|-------------|
| Wind Turbine | 35 | 15-45 | 25-55 | 8-15 | 650-690 |
| Gas Turbine | 20 | 20-50 | 350-450 | 3000-3600 | 11,000-13,800 |
| Substation | 15 | 5-20 | 20-40 | 0 | 132,000 |
| Solar Inverter | 20 | 2-10 | 30-60 | 0 | 600-800 |
| Hydro Unit | 10 | 25-55 | 35-65 | 200-500 | 11,000-22,000 |

---

## Technical Manuals Summary

### 1. Vestas V150-4.2MW Wind Turbine Manual
**Key Procedures:**
- Vibration bearing replacement (SKF-7320 bearing kit)
- Diagnostic criteria: Vibration > 80Hz for 24+ hours
- Parts list: Bearing kit, EP2 grease, torque wrench set, shaft seals
- Estimated duration: 6-8 hours (2 technicians)

### 2. GE 7HA.02 Gas Turbine Manual
**Key Procedures:**
- Compressor blade inspection (borescope)
- Temperature threshold: > 480°C for 2+ hours
- Inspection frequency: Every 4,000 operating hours
- Critical: Immediate shutdown if blade cracks detected

### 3. ABB 132kV GIS Substation Manual
**Key Procedures:**
- Arc flash safety (Category 3, 12 cal/cm²)
- Mandatory PPE: 40 cal/cm² suit, insulated gloves, arc hood
- SF6 gas leak detection (sensitivity: 1 ppm)
- Emergency: Defibrillator in control room

---

## Environment Variables

Create `.env` file:
```bash
# Databricks Connection
DATABRICKS_WORKSPACE=https://fe-sandbox-serverless-sandbox-tladem.cloud.databricks.com
DATABRICKS_PROFILE=fe-vm
DATABRICKS_WAREHOUSE_ID=a62624c51dced859

# Unity Catalog
CATALOG_NAME=serverless_sandbox_tladem_catalog
RAW_SCHEMA=mce_raw
SILVER_SCHEMA=mce_silver
GOLD_SCHEMA=mce_gold
AGENTS_SCHEMA=mce_agents
LAKEBASE_SCHEMA=mce_lakebase

# Lakebase (to be provisioned)
LAKEBASE_ENDPOINT_ID=<endpoint_id>
LAKEBASE_CONN_STRING=<secret_scope:mce-secrets/lakebase-conn-string>

# Agent Bricks
AGENT_ENDPOINT=<serving_endpoint_url>
```

---

## Next Steps

1. **Proceed to Workstream 2:**
   ```bash
   cd ../workstream-2-ingestion
   ```

2. **Build DLT Pipeline:**
   - Bronze: Streaming ingestion from volumes
   - Silver: Anomaly detection + asset registry join
   - Critical Alerts: Filter vibration > 80Hz

3. **Deploy Pipeline:**
   ```bash
   databricks pipelines create --config dlt_pipeline.json --profile fe-vm
   databricks pipelines start-update --pipeline-id <id> --profile fe-vm
   ```

4. **Monitor:**
   - Check event logs for schema evolution
   - Tune watermark/trigger intervals
   - Validate Critical_Alerts table population

---

## Project Structure

```
main-character-energy/
├── README.md (this file)
├── workstream-1-foundation/
│   ├── 01_catalog_setup.sql
│   ├── setup_catalog.py
│   ├── run_catalog_sql_v2.py
│   ├── generate_mock_data.py
│   ├── generate_pdf_manuals.py
│   ├── validate_setup.py
│   └── mock_data/
│       ├── sensor_telemetry.csv
│       ├── asset_registry.json
│       ├── maintenance_history.parquet
│       ├── vestas_v150_repair_manual.pdf
│       ├── ge_7ha_gas_turbine_manual.pdf
│       └── abb_substation_manual.pdf
├── workstream-2-ingestion/ (next)
├── workstream-3-intelligence/ (next)
├── workstream-4-lakebase/ (next)
├── workstream-5-app/ (next)
└── shared/
    ├── config/
    ├── secrets/
    └── utils/
```

---

## Support & References

- **Databricks MLOps Guide:** https://docs.databricks.com/mlflow/
- **Lakebase Docs:** https://docs.databricks.com/lakehouse-monitoring/
- **Agent Bricks Framework:** https://docs.databricks.com/generative-ai/agent-framework/
- **Workspace:** https://fe-sandbox-serverless-sandbox-tladem.cloud.databricks.com

---

## License

Internal use only - Main Character Energy © 2026
