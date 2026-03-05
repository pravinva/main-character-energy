#!/usr/bin/env python3
"""
Create Lakebase tables via Data API
"""

import requests
import json
import os

# Lakebase Data API endpoint
DATA_API_URL = "https://ep-tiny-field-d2xsbyci.database.us-east-1.cloud.databricks.com/api/2.0/workspace/7474651028007974/rest/databricks_postgres"
TOKEN = os.environ.get('DATABRICKS_TOKEN', '<YOUR_DATABRICKS_TOKEN>')

def execute_sql(sql, description=""):
    """Execute SQL via Lakebase Data API"""
    if description:
        print(f"  {description}...")

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "statement": sql
    }

    try:
        response = requests.post(DATA_API_URL, headers=headers, json=payload, timeout=60)

        if response.status_code == 200:
            print(f"    ✓ Success")
            return True
        else:
            print(f"    ✗ Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False

def main():
    print("Main Character Energy - Lakebase Data API Table Creation")
    print("=" * 60)

    # Create schema
    print("\n1. Creating schema mce_operations...")
    execute_sql(
        "CREATE SCHEMA IF NOT EXISTS mce_operations;",
        "Creating schema"
    )

    # Table 1: mce_assets_live_status
    print("\n2. Creating mce_assets_live_status...")
    execute_sql("""
        CREATE TABLE IF NOT EXISTS mce_operations.mce_assets_live_status (
            asset_id VARCHAR(50) PRIMARY KEY,
            site VARCHAR(200),
            asset_type VARCHAR(50),
            asset_name VARCHAR(200),
            vibration_hz DECIMAL(10,2),
            temp_celsius DECIMAL(10,2),
            rpm DECIMAL(10,2),
            voltage_output DECIMAL(15,2),
            status VARCHAR(20),
            predicted_failure_type VARCHAR(50),
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            active_work_order_id VARCHAR(50),
            hours_since_last_maintenance DECIMAL(10,2)
        );
    """, "Creating table")

    # Create indexes
    execute_sql(
        "CREATE INDEX IF NOT EXISTS idx_asset_status ON mce_operations.mce_assets_live_status(status);",
        "Creating status index"
    )
    execute_sql(
        "CREATE INDEX IF NOT EXISTS idx_asset_site ON mce_operations.mce_assets_live_status(site);",
        "Creating site index"
    )

    # Table 2: mce_work_orders
    print("\n3. Creating mce_work_orders...")
    execute_sql("""
        CREATE TABLE IF NOT EXISTS mce_operations.mce_work_orders (
            work_order_id VARCHAR(50) PRIMARY KEY,
            asset_id VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            priority VARCHAR(10),
            status VARCHAR(20),
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
    """, "Creating table")

    # Create indexes
    execute_sql(
        "CREATE INDEX IF NOT EXISTS idx_wo_status ON mce_operations.mce_work_orders(status);",
        "Creating status index"
    )
    execute_sql(
        "CREATE INDEX IF NOT EXISTS idx_wo_priority ON mce_operations.mce_work_orders(priority);",
        "Creating priority index"
    )

    # Table 3: mce_technicians
    print("\n4. Creating mce_technicians...")
    execute_sql("""
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
    """, "Creating table")

    # Create indexes
    execute_sql(
        "CREATE INDEX IF NOT EXISTS idx_tech_available ON mce_operations.mce_technicians(available);",
        "Creating available index"
    )

    # Seed technicians
    print("\n5. Seeding technician data...")
    execute_sql("""
        INSERT INTO mce_operations.mce_technicians
            (technician_id, name, site, certifications, available, active_work_orders)
        VALUES
            ('TECH-001', 'James Chen', 'Sydney North Wind Farm, NSW',
             '{"electrical": true, "wind_turbine": true, "high_voltage": true}', true, 0),
            ('TECH-002', 'Sarah Williams', 'Melbourne West Solar Park, VIC',
             '{"solar": true, "inverters": true}', true, 0),
            ('TECH-003', 'Michael ODonnell', 'Hunter Valley Gas Plant, NSW',
             '{"gas_turbine": true, "high_temp": true}', true, 0),
            ('TECH-004', 'Emma Thompson', 'Gippsland Hydro Station, VIC',
             '{"hydro": true, "mechanical": true}', true, 0),
            ('TECH-005', 'David Martinez', 'Broken Hill Solar Farm, NSW',
             '{"solar": true, "electrical": true}', true, 0),
            ('TECH-006', 'Lisa Anderson', 'Geelong Substation, VIC',
             '{"substation": true, "high_voltage": true}', true, 0),
            ('TECH-007', 'Tom Roberts', 'Newcastle Wind Farm, NSW',
             '{"wind_turbine": true, "mechanical": true}', true, 0),
            ('TECH-008', 'Rachel Kim', 'Yarra Valley Hydro, VIC',
             '{"hydro": true, "electrical": true}', true, 0)
        ON CONFLICT (technician_id) DO NOTHING;
    """, "Inserting 8 technicians")

    print("\n" + "=" * 60)
    print("✅ Lakebase tables created successfully!")
    print("\nTables in mce_operations schema:")
    print("  - mce_assets_live_status")
    print("  - mce_work_orders")
    print("  - mce_technicians")

if __name__ == "__main__":
    main()
