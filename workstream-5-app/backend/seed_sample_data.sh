#!/bin/bash
# Seed sample data into Lakebase
# Usage: PGPASSWORD='your-oauth-token' ./seed_sample_data.sh

if [ -z "$PGPASSWORD" ]; then
    echo "Error: PGPASSWORD environment variable must be set with OAuth token"
    echo "Usage: PGPASSWORD='your-oauth-token' ./seed_sample_data.sh"
    exit 1
fi

CONN="host=instance-b77ccee1-1d75-4ab9-9b52-4fe0de04ae5e.database.cloud.databricks.com user=pravin.varma@databricks.com dbname=databricks_postgres port=5432 sslmode=require"

echo "Seeding sample data..."

# Seed assets
echo "1. Seeding assets..."
psql "$CONN" << 'EOF'
INSERT INTO mce_operations.mce_assets_live_status
    (asset_id, asset_name, site, asset_type, vibration_hz, temp_celsius, rpm, voltage_output, status, predicted_failure_type, hours_since_last_maintenance, last_updated)
VALUES
    ('MCE-0001', 'Vestas V150-4.2MW Turbine 01', 'Sydney North Wind Farm, NSW', 'wind_turbine', 95.3, 48.2, 12.5, 680.0, 'CRITICAL', 'Bearing failure', 720, NOW()),
    ('MCE-0012', 'GE 7HA.02 Gas Turbine', 'Hunter Valley Gas Plant, NSW', 'gas_turbine', 88.1, 465.7, 3450.0, 13500.0, 'CRITICAL', 'Compressor blade', 980, NOW()),
    ('MCE-0034', 'ABB PVS800 Inverter 15', 'Broken Hill Solar Farm, NSW', 'solar_inverter', 85.7, 58.9, 0.0, 720.0, 'CRITICAL', 'Inverter overheating', 650, NOW()),
    ('MCE-0045', 'Vestas V90-3.0MW Turbine 22', 'Newcastle Wind Farm, NSW', 'wind_turbine', 72.4, 42.1, 13.2, 675.0, 'WARNING', 'Gearbox wear', 520, NOW()),
    ('MCE-0056', 'Siemens SWT-3.6-120 Turbine 05', 'Sydney North Wind Farm, NSW', 'wind_turbine', 68.9, 39.5, 12.8, 682.0, 'WARNING', 'Rotor imbalance', 450, NOW()),
    ('MCE-0067', 'Francis Turbine Unit 3', 'Gippsland Hydro Station, VIC', 'hydro_unit', 35.2, 48.7, 325.0, 18000.0, 'HEALTHY', NULL, 120, NOW()),
    ('MCE-0078', 'ABB 132kV GIS Substation Bay 4', 'Geelong Substation, VIC', 'substation', 12.5, 32.1, 0.0, 132000.0, 'HEALTHY', NULL, 200, NOW()),
    ('MCE-0089', 'SMA Sunny Central 2500', 'Melbourne West Solar Park, VIC', 'solar_inverter', 8.3, 38.9, 0.0, 750.0, 'HEALTHY', NULL, 180, NOW())
ON CONFLICT (asset_id) DO UPDATE SET
    vibration_hz = EXCLUDED.vibration_hz,
    temp_celsius = EXCLUDED.temp_celsius,
    status = EXCLUDED.status,
    last_updated = EXCLUDED.last_updated;
EOF

# Seed work orders
echo "2. Seeding work orders..."
psql "$CONN" << 'EOF'
INSERT INTO mce_operations.mce_work_orders
    (work_order_id, asset_id, priority, status, assigned_technician, predicted_failure_date, predicted_failure_type, required_parts, procedure_steps, safety_checklist, ai_repair_summary, estimated_duration_hours, created_at)
VALUES
    ('WO-001', 'MCE-0001', 'P1', 'DISPATCHED', 'James Chen', CURRENT_DATE + INTERVAL '2 days', 'Bearing failure', 'SKF-7320 bearing kit, EP2 grease', '1. Lock out turbine\n2. Remove nacelle cover\n3. Replace bearing assembly\n4. Torque to spec\n5. Test rotation', 'Fall protection harness, insulated gloves, lockout tags', 'Critical bearing replacement required. Vibration 95Hz exceeds safe threshold. High risk of catastrophic failure within 48 hours.', 8.0, NOW()),
    ('WO-002', 'MCE-0012', 'P1', 'IN_PROGRESS', 'Michael ODonnell', CURRENT_DATE + INTERVAL '1 day', 'Compressor blade', 'Compressor blade set (GE P/N 12345)', '1. Borescope inspection\n2. Document damage\n3. Replace damaged blades\n4. Balance rotor\n5. Test run', 'High temperature PPE (40 cal/cm²), eye protection, hearing protection', 'Blade damage detected via thermal imaging. Temperature 465°C exceeds normal range. Immediate repair required to prevent turbine shutdown.', 12.0, NOW()),
    ('WO-003', 'MCE-0034', 'P1', 'DISPATCHED', 'David Martinez', CURRENT_DATE + INTERVAL '3 days', 'Inverter overheating', 'Cooling fan assembly (ABB P/N 67890), thermal paste', '1. Power down inverter\n2. Replace cooling fans\n3. Clean heat sink\n4. Apply thermal compound\n5. Power up and monitor', 'Arc flash suit (Category 3), insulated tools, rubber mat', 'Thermal runaway risk detected. Inverter temperature 58.9°C approaching critical threshold. Cooling system failure imminent.', 4.0, NOW())
ON CONFLICT (work_order_id) DO NOTHING;
EOF

# Update technician availability
echo "3. Updating technician availability..."
psql "$CONN" << 'EOF'
UPDATE mce_operations.mce_technicians SET available = false, active_work_orders = 1, current_location = 'En route to MCE-0001' WHERE technician_id = 'TECH-001';
UPDATE mce_operations.mce_technicians SET available = false, active_work_orders = 1, current_location = 'At MCE-0012' WHERE technician_id = 'TECH-003';
UPDATE mce_operations.mce_technicians SET available = false, active_work_orders = 1, current_location = 'Broken Hill depot' WHERE technician_id = 'TECH-005';
EOF

# Verify
echo "4. Verifying data..."
psql "$CONN" << 'EOF'
SELECT
    'Assets' as table_name,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE status = 'CRITICAL') as critical,
    COUNT(*) FILTER (WHERE status = 'WARNING') as warning,
    COUNT(*) FILTER (WHERE status = 'HEALTHY') as healthy
FROM mce_operations.mce_assets_live_status
UNION ALL
SELECT
    'Work Orders',
    COUNT(*),
    COUNT(*) FILTER (WHERE priority = 'P1'),
    COUNT(*) FILTER (WHERE status = 'DISPATCHED'),
    COUNT(*) FILTER (WHERE status = 'IN_PROGRESS')
FROM mce_operations.mce_work_orders
UNION ALL
SELECT
    'Technicians',
    COUNT(*),
    COUNT(*) FILTER (WHERE available = true),
    COUNT(*) FILTER (WHERE active_work_orders > 0),
    0
FROM mce_operations.mce_technicians;
EOF

echo "✅ Sample data seeded successfully!"
