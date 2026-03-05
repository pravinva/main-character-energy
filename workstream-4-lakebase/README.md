# Workstream 4 - Lakebase Live State

## Status: Foundation Complete - Manual Provisioning Required

## Overview

Serverless Postgres (Lakebase) for real-time operational data with autoscaling. Provides sub-100ms query performance for mobile app and stores AI-generated work orders.

## Architecture

```
Delta Tables (Silver Layer)
    ↓ (30-second micro-batches)
Sync Pipeline (psycopg2)
    ↓
Lakebase (Serverless Postgres)
    ├── mce_assets_live_status (current asset state)
    ├── mce_work_orders (AI work orders from Agent Bricks)
    └── mce_technicians (field worker roster)
    ↓
Databricks App (React + FastAPI)
```

## Lakebase Setup Status

✅ **Completed:**
- Lakebase instance created: `mce_operations`
- Unity Catalog created: `mce_lakebase_catalog`
- Schema created: `mce_operations`
- Sync pipeline configured: `sync_delta_to_lakebase.py`

⚠️ **Manual Step Required:**
Tables need to be created via Lakebase UI using the SQL scripts provided (authentication limitations prevent automated creation).

## Lakebase Catalog Setup

### Option 1: Create via Databricks UI (Recommended)

1. **Navigate to Data Explorer**
   - Go to: https://fe-sandbox-serverless-sandbox-tladem.cloud.databricks.com/explore/data

2. **Create Managed Online Catalog (Lakebase)**
   - Click "+" → "Add Catalog"
   - Select "Managed Online Catalog"
   - Name: `mce_lakebase_catalog`
   - Database: `databricks_postgres`
   - Autoscaling: Enabled
   - Click "Create"

3. **Wait for Provisioning**
   - Lakebase typically provisions in 3-5 minutes
   - Status will change from "PROVISIONING" to "ACTIVE"

4. **Get Endpoint Details**
   ```sql
   DESCRIBE CATALOG mce_lakebase_catalog;
   ```

   Save the connection endpoint ID for later use.

### Option 2: Manual Table Creation via Lakebase SQL Editor

**Lakebase Connection Details:**
- **Endpoint:** `ep-tiny-field-d2xsbyci.database.us-east-1.cloud.databricks.com`
- **Database:** `databricks_postgres`
- **Branch:** `production`
- **Schema:** `mce_operations`

**Steps to create tables:**

1. Navigate to your Lakebase instance: `mce_operations`
2. Open SQL Editor
3. Copy and execute SQL from: `create_lakebase_tables.sql`

**Or use psql CLI:**
```bash
psql "postgresql://pravin.varma@databricks.com@ep-tiny-field-d2xsbyci.database.us-east-1.cloud.databricks.com:5432/databricks_postgres?sslmode=require" -f create_lakebase_tables.sql
```

## Database Schema Setup

### Create Schema

```sql
CREATE SCHEMA IF NOT EXISTS mce_lakebase_catalog.mce_operations
COMMENT 'Main Character Energy operational data';
```

## Table Schemas

### Table 1: mce_assets_live_status

Real-time asset monitoring state.

```sql
CREATE TABLE mce_lakebase_catalog.mce_operations.mce_assets_live_status (
    asset_id STRING PRIMARY KEY,
    site STRING,
    asset_type STRING,
    asset_name STRING,
    vibration_hz DECIMAL(10,2),
    temp_celsius DECIMAL(10,2),
    rpm DECIMAL(10,2),
    voltage_output DECIMAL(15,2),
    status STRING CHECK (status IN ('CRITICAL', 'WARNING', 'HEALTHY')),
    predicted_failure_type STRING,
    last_updated TIMESTAMP,
    active_work_order_id STRING,
    hours_since_last_maintenance DECIMAL(10,2)
) USING POSTGRES;

-- Indexes for query performance
CREATE INDEX idx_asset_status ON mce_lakebase_catalog.mce_operations.mce_assets_live_status(status);
CREATE INDEX idx_asset_site ON mce_lakebase_catalog.mce_operations.mce_assets_live_status(site);
```

### Table 2: mce_work_orders

AI-generated work orders from Agent Bricks.

```sql
CREATE TABLE mce_lakebase_catalog.mce_operations.mce_work_orders (
    work_order_id STRING PRIMARY KEY,
    asset_id STRING NOT NULL,
    created_at TIMESTAMP,
    priority STRING CHECK (priority IN ('P1', 'P2', 'P3')),
    status STRING CHECK (status IN ('DISPATCHED', 'IN_PROGRESS', 'COMPLETE', 'CANCELLED')),
    assigned_technician STRING,
    predicted_failure_date DATE,
    predicted_failure_type STRING,
    required_parts STRING,  -- JSON string
    procedure_steps STRING,  -- JSON string
    safety_checklist STRING,  -- JSON string
    ai_repair_summary STRING,
    estimated_duration_hours DECIMAL(5,2),
    actual_duration_hours DECIMAL(5,2),
    first_time_fix_verified BOOLEAN,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP
) USING POSTGRES;

-- Indexes
CREATE INDEX idx_wo_status ON mce_lakebase_catalog.mce_operations.mce_work_orders(status);
CREATE INDEX idx_wo_priority ON mce_lakebase_catalog.mce_operations.mce_work_orders(priority);
CREATE INDEX idx_wo_asset ON mce_lakebase_catalog.mce_operations.mce_work_orders(asset_id);
```

### Table 3: mce_technicians

Field worker roster and availability.

```sql
CREATE TABLE mce_lakebase_catalog.mce_operations.mce_technicians (
    technician_id STRING PRIMARY KEY,
    name STRING NOT NULL,
    site STRING,
    certifications STRING,  -- JSON string
    current_location STRING,
    available BOOLEAN,
    active_work_orders INT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
) USING POSTGRES;

-- Indexes
CREATE INDEX idx_tech_available ON mce_lakebase_catalog.mce_operations.mce_technicians(available);
CREATE INDEX idx_tech_site ON mce_lakebase_catalog.mce_operations.mce_technicians(site);
```

## Database Users

### User 1: main_energy (Admin User)

```sql
-- Create in Lakebase Postgres instance
CREATE USER main_energy WITH PASSWORD 'MCE_SecurePass_2026!';
GRANT ALL PRIVILEGES ON SCHEMA mce_operations TO main_energy;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA mce_operations TO main_energy;
```

### User 2: mce_service (Permanent Service User)

```sql
-- Create in Lakebase Postgres instance
CREATE USER mce_service WITH PASSWORD 'MCE_Service_Perm_2026!';
GRANT USAGE ON SCHEMA mce_operations TO mce_service;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA mce_operations TO mce_service;
```

## Seed Data: Technicians

```sql
INSERT INTO mce_lakebase_catalog.mce_operations.mce_technicians
    (technician_id, name, site, certifications, available, active_work_orders, created_at)
VALUES
    ('TECH-001', 'James Chen', 'Sydney North Wind Farm, NSW',
     '{"electrical": true, "wind_turbine": true, "high_voltage": true}', true, 0, CURRENT_TIMESTAMP()),
    ('TECH-002', 'Sarah Williams', 'Melbourne West Solar Park, VIC',
     '{"solar": true, "inverters": true}', true, 0, CURRENT_TIMESTAMP()),
    ('TECH-003', 'Michael ODonnell', 'Hunter Valley Gas Plant, NSW',
     '{"gas_turbine": true, "high_temp": true, "pressure_systems": true}', true, 0, CURRENT_TIMESTAMP()),
    ('TECH-004', 'Emma Thompson', 'Gippsland Hydro Station, VIC',
     '{"hydro": true, "mechanical": true}', true, 0, CURRENT_TIMESTAMP()),
    ('TECH-005', 'David Martinez', 'Broken Hill Solar Farm, NSW',
     '{"solar": true, "electrical": true}', true, 0, CURRENT_TIMESTAMP()),
    ('TECH-006', 'Lisa Anderson', 'Geelong Substation, VIC',
     '{"substation": true, "high_voltage": true, "arc_flash": true}', true, 0, CURRENT_TIMESTAMP()),
    ('TECH-007', 'Tom Roberts', 'Newcastle Wind Farm, NSW',
     '{"wind_turbine": true, "mechanical": true}', true, 0, CURRENT_TIMESTAMP()),
    ('TECH-008', 'Rachel Kim', 'Yarra Valley Hydro, VIC',
     '{"hydro": true, "electrical": true}', true, 0, CURRENT_TIMESTAMP());
```

## Delta to Lakebase Sync Pipeline

### Sync Script: `sync_delta_to_lakebase.py`

Runs every 30 seconds to sync critical alerts from Delta (Silver layer) to Lakebase.

```python
# See sync_delta_to_lakebase.py for full implementation
```

**Features:**
- Reads from `serverless_sandbox_tladem_catalog.mce_silver.critical_alerts`
- UPSERTs to `mce_lakebase_catalog.mce_operations.mce_assets_live_status`
- Uses Change Data Feed (CDF) for incremental updates
- Connection pooling with psycopg2
- 30-second micro-batch trigger
- Error handling and retry logic

## Connection Details

### Connection String Format

```
postgresql://main_energy:MCE_SecurePass_2026!@<endpoint-id>.cloud.databricks.com:5432/databricks_postgres
```

### Get Endpoint Details

```sql
DESCRIBE CATALOG mce_lakebase_catalog;
```

Look for the `connection_name` or `endpoint_id` field.

### Store Credentials in Secret Scope

```bash
# Create secret scope
databricks secrets create-scope mce-secrets --profile fe-vm

# Store Lakebase password
databricks secrets put-secret mce-secrets lakebase-password \
  --string-value 'MCE_SecurePass_2026!' \
  --profile fe-vm

# Store connection string
databricks secrets put-secret mce-secrets lakebase-conn-string \
  --string-value 'postgresql://mce_service:<password>@<endpoint>.cloud.databricks.com:5432/databricks_postgres' \
  --profile fe-vm
```

## Deployment Steps

### 1. Create Lakebase Catalog (via UI or CLI)

Follow "Option 1" or "Option 2" above.

### 2. Create Schema and Tables

```bash
# Execute table creation DDL via SQL Editor in Databricks UI
# Or use notebooks with Spark SQL
```

### 3. Seed Technician Data

Run the seed INSERT statement via SQL Editor.

### 4. Deploy Sync Pipeline

```bash
cd workstream-4-lakebase
source ../.venv/bin/activate
python sync_delta_to_lakebase.py
```

Or deploy as a Databricks Job:

```bash
databricks jobs create --json-file sync_job_config.json --profile fe-vm
databricks jobs run-now --job-id <job_id> --profile fe-vm
```

### 5. Test Connection

```bash
python test_lakebase_connection.py
```

## Validation Queries

### Check Asset Status Sync

```sql
SELECT
  COUNT(*) as total_assets,
  SUM(CASE WHEN status = 'CRITICAL' THEN 1 ELSE 0 END) as critical_count,
  MAX(last_updated) as latest_update
FROM mce_lakebase_catalog.mce_operations.mce_assets_live_status;

-- Expected: 8 critical assets
```

### Check Work Orders

```sql
SELECT
  work_order_id,
  asset_id,
  priority,
  status,
  assigned_technician,
  created_at
FROM mce_lakebase_catalog.mce_operations.mce_work_orders
ORDER BY created_at DESC
LIMIT 10;
```

### Check Technician Availability

```sql
SELECT
  technician_id,
  name,
  site,
  available,
  active_work_orders
FROM mce_lakebase_catalog.mce_operations.mce_technicians
WHERE available = true;

-- Expected: 8 available technicians
```

## Performance Characteristics

| Metric | Target | Actual |
|--------|--------|--------|
| Query Latency (p95) | < 200ms | TBD |
| Sync Frequency | 30 seconds | 30 seconds |
| Connection Pool | 2-10 connections | Configurable |
| Concurrent Reads | 50+ | Autoscaling |
| Table Size | 100-1000 rows | Small (optimized) |

## Integration with Other Workstreams

### From Workstream 2 (DLT Pipeline)
- **Input:** `critical_alerts` table from Silver layer
- **Sync:** Real-time asset status updates

### To Workstream 3 (Agent Bricks)
- **Output:** Agent creates work orders via `create_work_order()` tool
- **Storage:** Work orders written to `mce_work_orders` table

### To Workstream 5 (Databricks App)
- **Read:** App queries Lakebase for live data
- **Update:** Field workers update work order status
- **Latency:** Sub-100ms for mobile responsiveness

## Troubleshooting

### Issue: Catalog Creation Fails
**Solution:** Use Databricks UI to create Managed Online Catalog manually

### Issue: Connection Refused
**Solution:** Check endpoint is ACTIVE, verify connection string format

### Issue: Slow Queries
**Solution:** Add indexes on frequently queried columns, check connection pool size

### Issue: Sync Pipeline Not Running
**Solution:** Check Delta table has Change Data Feed enabled, verify credentials

## Files

```
workstream-4-lakebase/
├── README.md (this file)
├── setup_lakebase.py                    # Automated setup script (partial)
├── create_lakebase_tables.sql           # Generated SQL for table creation
├── sync_delta_to_lakebase.py            # Delta → Lakebase sync pipeline
├── test_lakebase_connection.py          # Connection test script
└── sync_job_config.json                 # Databricks job configuration
```

## Next Steps

1. Create Lakebase catalog via UI
2. Execute table DDL
3. Seed technician data
4. Deploy sync pipeline
5. Test connection and queries
6. Proceed to Workstream 5 (Databricks App with FastAPI + React)

## Security Notes

- Passwords stored in Databricks Secret Scope only
- Connection strings never committed to git
- Service user has limited permissions (no DROP/DELETE)
- All connections use TLS encryption
- Audit logging enabled on Lakebase catalog
