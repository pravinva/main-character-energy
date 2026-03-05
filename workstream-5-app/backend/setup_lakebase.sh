#!/bin/bash
# Setup Lakebase tables using OAuth token
# Usage: PGPASSWORD='your-oauth-token' ./setup_lakebase.sh

if [ -z "$PGPASSWORD" ]; then
    echo "Error: PGPASSWORD environment variable must be set with OAuth token"
    echo "Usage: PGPASSWORD='your-oauth-token' ./setup_lakebase.sh"
    exit 1
fi

CONN="host=instance-b77ccee1-1d75-4ab9-9b52-4fe0de04ae5e.database.cloud.databricks.com user=pravin.varma@databricks.com dbname=databricks_postgres port=5432 sslmode=require"

echo "Creating Lakebase tables..."

# Create mce_assets_live_status
echo "1. Creating mce_assets_live_status..."
psql "$CONN" << 'EOF'
CREATE TABLE IF NOT EXISTS mce_operations.mce_assets_live_status (
    asset_id VARCHAR(50) PRIMARY KEY,
    site VARCHAR(200),
    asset_type VARCHAR(50),
    asset_name VARCHAR(200),
    vibration_hz DECIMAL(10,2),
    temp_celsius DECIMAL(10,2),
    rpm DECIMAL(10,2),
    voltage_output DECIMAL(15,2),
    status VARCHAR(20) CHECK (status IN ('CRITICAL', 'WARNING', 'HEALTHY')),
    predicted_failure_type VARCHAR(50),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    active_work_order_id VARCHAR(50),
    hours_since_last_maintenance DECIMAL(10,2)
);
CREATE INDEX IF NOT EXISTS idx_asset_status ON mce_operations.mce_assets_live_status(status);
CREATE INDEX IF NOT EXISTS idx_asset_site ON mce_operations.mce_assets_live_status(site);
EOF

# Create mce_work_orders
echo "2. Creating mce_work_orders..."
psql "$CONN" << 'EOF'
CREATE TABLE IF NOT EXISTS mce_operations.mce_work_orders (
    work_order_id VARCHAR(50) PRIMARY KEY,
    asset_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    priority VARCHAR(10) CHECK (priority IN ('P1', 'P2', 'P3')),
    status VARCHAR(20) CHECK (status IN ('DISPATCHED', 'IN_PROGRESS', 'COMPLETE', 'CANCELLED')),
    assigned_technician VARCHAR(200),
    predicted_failure_date DATE,
    predicted_failure_type VARCHAR(50),
    required_parts TEXT,
    procedure_steps TEXT,
    safety_checklist TEXT,
    ai_repair_summary TEXT,
    estimated_duration_hours DECIMAL(5,2),
    actual_duration_hours DECIMAL(5,2),
    first_time_fix_verified BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_wo_status ON mce_operations.mce_work_orders(status);
CREATE INDEX IF NOT EXISTS idx_wo_priority ON mce_operations.mce_work_orders(priority);
EOF

# Create mce_technicians
echo "3. Creating mce_technicians..."
psql "$CONN" << 'EOF'
CREATE TABLE IF NOT EXISTS mce_operations.mce_technicians (
    technician_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    site VARCHAR(200),
    certifications TEXT,
    current_location TEXT,
    available BOOLEAN DEFAULT TRUE,
    active_work_orders INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_tech_available ON mce_operations.mce_technicians(available);
EOF

# Seed technicians
echo "4. Seeding technicians..."
psql "$CONN" << 'EOF'
INSERT INTO mce_operations.mce_technicians
    (technician_id, name, site, certifications, available, active_work_orders)
VALUES
    ('TECH-001', 'James Chen', 'Sydney North Wind Farm, NSW', '{"electrical": true, "wind_turbine": true}', true, 0),
    ('TECH-002', 'Sarah Williams', 'Melbourne West Solar Park, VIC', '{"solar": true, "inverters": true}', true, 0),
    ('TECH-003', 'Michael ODonnell', 'Hunter Valley Gas Plant, NSW', '{"gas_turbine": true}', true, 0),
    ('TECH-004', 'Emma Thompson', 'Gippsland Hydro Station, VIC', '{"hydro": true}', true, 0),
    ('TECH-005', 'David Martinez', 'Broken Hill Solar Farm, NSW', '{"solar": true}', true, 0),
    ('TECH-006', 'Lisa Anderson', 'Geelong Substation, VIC', '{"substation": true}', true, 0),
    ('TECH-007', 'Tom Roberts', 'Newcastle Wind Farm, NSW', '{"wind_turbine": true}', true, 0),
    ('TECH-008', 'Rachel Kim', 'Yarra Valley Hydro, VIC', '{"hydro": true}', true, 0)
ON CONFLICT (technician_id) DO NOTHING;
EOF

# Verify
echo "5. Verifying setup..."
psql "$CONN" -c "SELECT COUNT(*) as technician_count FROM mce_operations.mce_technicians;"

echo "✅ Lakebase setup complete!"
