# Workstream 2 - Lakeflow DLT Ingestion Pipelines

## Overview

Delta Live Tables (DLT) pipeline that ingests sensor telemetry, enriches with asset data, and generates critical alerts for the Agent Bricks system.

## Pipeline Architecture

```
Volumes (CSV/JSON/Parquet)
    ↓
Bronze Layer (Raw + Metadata)
    ↓
Silver Layer (Cleaned + Enriched + Anomaly Detection)
    ↓
Critical Alerts + Gold Aggregates
```

## Tables Created

### Bronze Layer

| Table | Type | Source | Description |
|-------|------|--------|-------------|
| `bronze_telemetry` | Streaming | Volume CSV | Raw sensor readings with ingestion metadata |
| `bronze_asset_registry` | Batch | Volume JSON | Master asset list |
| `bronze_maintenance_history` | Batch | Volume Parquet | Historical maintenance events |

### Silver Layer

| Table | Type | Description |
|-------|------|-------------|
| `silver_asset_telemetry` | Streaming | Telemetry joined with registry, enriched with anomaly flags and maintenance history |
| `critical_alerts` | Streaming | Filtered view of CRITICAL assets (vibration > 80Hz or temp anomalies) |

**Silver Schema:**
- All bronze telemetry columns
- Asset registry fields (model, serial_number, assigned_technician, manual_version)
- `hours_since_last_maintenance` (calculated)
- `vibration_anomaly` (CRITICAL/WARNING/NORMAL)
- `temperature_anomaly` (CRITICAL/WARNING/NORMAL based on asset type)
- `overall_status` (CRITICAL/WARNING/HEALTHY)
- `processed_timestamp`

**Critical Alerts Schema:**
- Core telemetry + asset fields
- `alert_severity`: CRITICAL
- `alert_timestamp`: When alert was generated
- `predicted_failure_type`: BEARING_FAILURE | COOLING_FAULT | GENERAL_ANOMALY

### Gold Layer

| Table | Type | Description |
|-------|------|-------------|
| `gold_asset_health_summary` | Batch | Daily aggregates by site/asset_type/status |
| `gold_critical_assets_daily` | Batch | Daily critical asset counts with failure type breakdown |

## Anomaly Detection Rules

### Vibration Anomaly
- **CRITICAL:** vibration_hz > 80
- **WARNING:** vibration_hz > 60
- **NORMAL:** vibration_hz ≤ 60

### Temperature Anomaly (Asset-Type Specific)
- **Wind Turbine:** CRITICAL if temp > 70°C
- **Gas Turbine:** CRITICAL if temp > 480°C
- **General:** WARNING if temp > 100°C

### Overall Status
- **CRITICAL:** Any CRITICAL anomaly
- **WARNING:** Any WARNING anomaly (no CRITICAL)
- **HEALTHY:** All readings normal

## Data Quality Expectations

### Bronze Layer
- `valid_asset_id`: asset_id IS NOT NULL
- `valid_vibration`: vibration_hz BETWEEN 0 AND 500
- `valid_temperature`: temp_celsius BETWEEN -50 AND 1000

**Action:** Drop rows that fail validation

### Silver Layer
- `no_nulls_asset_id`: asset_id IS NOT NULL
- `join_successful`: model IS NOT NULL (ensures asset registry join worked)

**Action:** Track quality metrics (expectations mode)

## Deployment

### Prerequisites
1. Workstream 1 complete (catalog + volumes with data)
2. Databricks workspace with serverless compute enabled
3. Profile: `fe-vm`

### Deploy Pipeline

```bash
cd workstream-2-ingestion
source ../.venv/bin/activate
python deploy_pipeline.py
```

The deployment script will:
1. Upload DLT notebook to workspace
2. Create pipeline with serverless compute
3. Trigger full refresh
4. Monitor progress
5. Validate output tables

### Manual Deployment (Alternative)

If automated deployment fails, use Databricks UI:

1. **Upload Notebook:**
   ```bash
   databricks workspace import \
     /Users/pravin.varma@databricks.com/main-character-energy/mce_dlt_pipeline \
     --file mce_dlt_pipeline.py \
     --language PYTHON \
     --format SOURCE \
     --profile fe-vm
   ```

2. **Create Pipeline via UI:**
   - Go to Workflows → Delta Live Tables
   - Click "Create Pipeline"
   - Name: `mce_telemetry_ingestion`
   - Notebook: `/Users/pravin.varma@databricks.com/main-character-energy/mce_dlt_pipeline`
   - Target: `serverless_sandbox_tladem_catalog.mce_silver`
   - Catalog: `serverless_sandbox_tladem_catalog`
   - Compute: Serverless
   - Edition: Advanced
   - Photon: Enabled

3. **Start Pipeline:**
   - Click "Start" → "Full Refresh"

## Validation Queries

After pipeline runs successfully:

```sql
-- Check bronze ingestion
SELECT COUNT(*) FROM serverless_sandbox_tladem_catalog.mce_silver.bronze_telemetry;

-- Check silver enrichment
SELECT COUNT(*) FROM serverless_sandbox_tladem_catalog.mce_silver.silver_asset_telemetry;

-- Check critical alerts
SELECT
  asset_id,
  asset_name,
  site,
  vibration_hz,
  predicted_failure_type,
  alert_timestamp
FROM serverless_sandbox_tladem_catalog.mce_silver.critical_alerts
ORDER BY vibration_hz DESC;

-- Expected: 8 critical assets

-- Asset health distribution
SELECT
  overall_status,
  COUNT(DISTINCT asset_id) as asset_count
FROM serverless_sandbox_tladem_catalog.mce_silver.silver_asset_telemetry
GROUP BY overall_status;

-- Expected: CRITICAL=8, WARNING=5, HEALTHY=87
```

## Pipeline Monitoring

### DLT Event Log

Check pipeline health:
```sql
SELECT
  timestamp,
  level,
  message
FROM event_log('mce_telemetry_ingestion')
WHERE level IN ('ERROR', 'WARN')
ORDER BY timestamp DESC
LIMIT 100;
```

### Data Quality Metrics

```sql
-- Expectation failures
SELECT
  name,
  dataset,
  failed_records,
  passed_records
FROM event_log('mce_telemetry_ingestion')
WHERE details:flow_progress.metrics IS NOT NULL;
```

## Troubleshooting

### Issue: Schema Evolution Errors
**Solution:** Add `cloudFiles.schemaEvolutionMode` = `rescue` to bronze layer

### Issue: Join Failures (model IS NULL)
**Solution:** Verify asset_registry.json has matching asset_ids

### Issue: No Critical Alerts Generated
**Solution:** Check if mock data has vibration > 80Hz (should be 8 assets)

### Issue: Pipeline Fails to Start
**Solution:** Ensure serverless compute is enabled, catalog parameter is set

## Next Steps

Once pipeline is running successfully:

1. **Verify Critical Alerts Table Populated**
   ```sql
   SELECT COUNT(*) FROM serverless_sandbox_tladem_catalog.mce_silver.critical_alerts;
   -- Should return 8
   ```

2. **Proceed to Workstream 3**
   - Build Agent Bricks that reads from `critical_alerts`
   - Vector search over PDF manuals
   - Generate smart work orders

## Files

```
workstream-2-ingestion/
├── README.md (this file)
├── mce_dlt_pipeline.py         # DLT pipeline code
├── deploy_pipeline.py           # Automated deployment script
└── pipeline_config.json         # Pipeline configuration (reference)
```

## Configuration

Target Catalog: `serverless_sandbox_tladem_catalog`
Target Schema: `mce_silver`
Compute: Serverless
Photon: Enabled
CDC: Enabled on silver tables
Continuous: False (triggered mode)
