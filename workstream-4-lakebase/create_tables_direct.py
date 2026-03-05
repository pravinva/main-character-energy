#!/usr/bin/env python3
"""
Create Lakebase tables via direct Postgres connection
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import getpass
import os
import sys

# Lakebase connection details
HOST = "ep-tiny-field-d2xsbyci.database.us-east-1.cloud.databricks.com"
PORT = 5432
DATABASE = "databricks_postgres"
USER = "token"  # Use 'token' as username for PAT authentication
SSLMODE = "require"

def main():
    print("Main Character Energy - Lakebase Direct Table Creation")
    print("=" * 60)

    # Use Databricks token from environment variable
    password = os.environ.get('DATABRICKS_TOKEN', '<YOUR_DATABRICKS_TOKEN>')
    if password == '<YOUR_DATABRICKS_TOKEN>':
        print("✗ Error: DATABRICKS_TOKEN environment variable not set")
        print("Set it with: export DATABRICKS_TOKEN='your_token'")
        return 1
    print(f"Using Databricks token authentication for {USER}")

    # Build connection string with proper URL encoding
    from urllib.parse import quote_plus
    user_encoded = quote_plus(USER)
    password_encoded = quote_plus(password)
    conn_string = f"postgresql://{user_encoded}:{password_encoded}@{HOST}:{PORT}/{DATABASE}?sslmode={SSLMODE}"

    try:
        print(f"\nConnecting to Lakebase at {HOST}...")
        conn = psycopg2.connect(conn_string)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        print("  ✓ Connected successfully")

        # Create schema
        print("\n1. Creating schema mce_operations...")
        cursor.execute("""
            CREATE SCHEMA IF NOT EXISTS mce_operations;
        """)
        print("  ✓ Schema created")

        # Table 1: mce_assets_live_status
        print("\n2. Creating table mce_assets_live_status...")
        cursor.execute("""
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
        """)
        print("  ✓ Table created")

        # Create indexes for mce_assets_live_status
        print("    Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_asset_status ON mce_operations.mce_assets_live_status(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_asset_site ON mce_operations.mce_assets_live_status(site);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_last_updated ON mce_operations.mce_assets_live_status(last_updated);")
        print("  ✓ Indexes created")

        # Table 2: mce_work_orders
        print("\n3. Creating table mce_work_orders...")
        cursor.execute("""
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
        """)
        print("  ✓ Table created")

        # Create indexes for mce_work_orders
        print("    Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wo_status ON mce_operations.mce_work_orders(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wo_priority ON mce_operations.mce_work_orders(priority);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wo_asset ON mce_operations.mce_work_orders(asset_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wo_technician ON mce_operations.mce_work_orders(assigned_technician);")
        print("  ✓ Indexes created")

        # Table 3: mce_technicians
        print("\n4. Creating table mce_technicians...")
        cursor.execute("""
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
        """)
        print("  ✓ Table created")

        # Create indexes for mce_technicians
        print("    Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tech_available ON mce_operations.mce_technicians(available);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tech_site ON mce_operations.mce_technicians(site);")
        print("  ✓ Indexes created")

        # Create database users for service access
        print("\n5. Creating database users...")
        try:
            cursor.execute("""
                CREATE USER mce_service WITH PASSWORD 'MCE_Service_2026!';
            """)
            cursor.execute("""
                GRANT CONNECT ON DATABASE databricks_postgres TO mce_service;
            """)
            cursor.execute("""
                GRANT USAGE ON SCHEMA mce_operations TO mce_service;
            """)
            cursor.execute("""
                GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA mce_operations TO mce_service;
            """)
            print("  ✓ User 'mce_service' created (password: MCE_Service_2026!)")
        except Exception as e:
            if "already exists" in str(e):
                print("  ℹ️  User 'mce_service' already exists")
            else:
                print(f"  ⚠️  Error creating user: {e}")

        # Seed technicians
        print("\n6. Seeding technician data...")
        cursor.execute("""
            INSERT INTO mce_operations.mce_technicians
                (technician_id, name, site, certifications, available, active_work_orders, created_at)
            VALUES
                ('TECH-001', 'James Chen', 'Sydney North Wind Farm, NSW',
                 '{"electrical": true, "wind_turbine": true, "high_voltage": true}', true, 0, CURRENT_TIMESTAMP),
                ('TECH-002', 'Sarah Williams', 'Melbourne West Solar Park, VIC',
                 '{"solar": true, "inverters": true}', true, 0, CURRENT_TIMESTAMP),
                ('TECH-003', 'Michael ODonnell', 'Hunter Valley Gas Plant, NSW',
                 '{"gas_turbine": true, "high_temp": true, "pressure_systems": true}', true, 0, CURRENT_TIMESTAMP),
                ('TECH-004', 'Emma Thompson', 'Gippsland Hydro Station, VIC',
                 '{"hydro": true, "mechanical": true}', true, 0, CURRENT_TIMESTAMP),
                ('TECH-005', 'David Martinez', 'Broken Hill Solar Farm, NSW',
                 '{"solar": true, "electrical": true}', true, 0, CURRENT_TIMESTAMP),
                ('TECH-006', 'Lisa Anderson', 'Geelong Substation, VIC',
                 '{"substation": true, "high_voltage": true, "arc_flash": true}', true, 0, CURRENT_TIMESTAMP),
                ('TECH-007', 'Tom Roberts', 'Newcastle Wind Farm, NSW',
                 '{"wind_turbine": true, "mechanical": true}', true, 0, CURRENT_TIMESTAMP),
                ('TECH-008', 'Rachel Kim', 'Yarra Valley Hydro, VIC',
                 '{"hydro": true, "electrical": true}', true, 0, CURRENT_TIMESTAMP)
            ON CONFLICT (technician_id) DO NOTHING;
        """)
        print("  ✓ Seeded 8 technicians")

        cursor.close()
        conn.close()

        print("\n" + "=" * 60)
        print("✅ Lakebase tables created successfully!")
        print("\nTables in mce_operations schema:")
        print("  - mce_assets_live_status (live asset monitoring)")
        print("  - mce_work_orders (AI-generated work orders)")
        print("  - mce_technicians (field worker roster)")

        print(f"\nConnection endpoint: {HOST}")
        print(f"Database: {DATABASE}")
        print(f"Schema: mce_operations")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
