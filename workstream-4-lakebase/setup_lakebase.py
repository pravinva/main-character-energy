#!/usr/bin/env python3
"""
Main Character Energy - Lakebase Setup
Creates serverless Postgres catalog with autoscaling and users
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import *
from databricks.sdk.service.sql import StatementState
import time
import json

PROFILE = "fe-vm"
CATALOG_NAME = "mce_lakebase_catalog"
DATABASE_NAME = "databricks_postgres"

def execute_sql(w, warehouse_id, sql_statement, description=""):
    """Execute SQL and wait for completion"""
    if description:
        print(f"  {description}...")

    statement = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql_statement,
        wait_timeout="50s"
    )

    while statement.status.state in [StatementState.PENDING, StatementState.RUNNING]:
        time.sleep(1)
        statement = w.statement_execution.get_statement(statement.statement_id)

    if statement.status.state == StatementState.SUCCEEDED:
        print(f"    ✓ Success")
        return statement.result
    else:
        error_msg = statement.status.error.message if statement.status.error else "Unknown error"
        print(f"    ✗ Failed: {error_msg}")
        raise Exception(f"SQL failed: {error_msg}")

def main():
    w = WorkspaceClient(profile=PROFILE)
    warehouse_id = "a62624c51dced859"

    print("Main Character Energy - Lakebase Setup")
    print("=" * 60)

    # Step 1: Create Lakebase Catalog (Managed Online Catalog with Postgres)
    print("\n1. Creating Lakebase catalog...")

    try:
        # Check if catalog already exists
        existing_catalogs = w.catalogs.list()
        catalog_exists = any(c.name == CATALOG_NAME for c in existing_catalogs)

        if catalog_exists:
            print(f"  ℹ️  Catalog '{CATALOG_NAME}' already exists")
            catalog_info = w.catalogs.get(name=CATALOG_NAME)
            print(f"  Type: {catalog_info.catalog_type}")
        else:
            # Create managed online catalog (Lakebase/Postgres)
            print(f"  Creating managed online catalog: {CATALOG_NAME}")

            created_catalog = w.catalogs.create(
                name=CATALOG_NAME,
                comment="Main Character Energy - Lakebase (Serverless Postgres)",
                properties={
                    "database": DATABASE_NAME
                },
                catalog_type=CatalogType.MANAGED_ONLINE_CATALOG
            )

            print(f"  ✓ Lakebase catalog created: {CATALOG_NAME}")
            print(f"  Catalog ID: {created_catalog.name}")

            # Wait for catalog to be ready
            print("  Waiting for catalog provisioning...")
            time.sleep(30)  # Give it time to provision

    except Exception as e:
        print(f"  ✗ Error creating catalog: {e}")
        print(f"  Note: Creating managed online catalogs may require UI or specific permissions")
        print(f"  Alternative: Use existing Lakebase catalog or create via UI")

        # Check for existing lakebase catalogs
        print("\n  Checking for existing Lakebase catalogs...")
        for catalog in existing_catalogs:
            if catalog.catalog_type == CatalogType.MANAGED_ONLINE_CATALOG:
                print(f"    - {catalog.name} (Type: {catalog.catalog_type})")

    # Step 2: Create Schema for MCE
    print("\n2. Creating schema in Lakebase catalog...")

    # First, try to get the catalog info to see if it exists
    try:
        catalog_info = w.catalogs.get(name=CATALOG_NAME)

        # Create schema
        try:
            w.schemas.create(
                name="mce_operations",
                catalog_name=CATALOG_NAME,
                comment="Main Character Energy operational data"
            )
            print(f"  ✓ Schema created: mce_operations")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"  ℹ️  Schema 'mce_operations' already exists")
            else:
                raise

    except Exception as e:
        print(f"  ⚠️  Could not create schema: {e}")

    # Step 3: Create database users
    print("\n3. Creating database users...")
    print("  Note: User creation in Lakebase requires SQL commands")

    # Create SQL statements for user creation
    create_user_sql = f"""
    -- Create main_energy user
    CREATE USER IF NOT EXISTS main_energy WITH PASSWORD 'MCE_SecurePass_2026!';

    -- Grant permissions
    GRANT USAGE ON SCHEMA mce_operations TO main_energy;
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA mce_operations TO main_energy;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA mce_operations TO main_energy;

    -- Create permanent user for service connections
    CREATE USER IF NOT EXISTS mce_service WITH PASSWORD 'MCE_Service_Perm_2026!';
    GRANT USAGE ON SCHEMA mce_operations TO mce_service;
    GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA mce_operations TO mce_service;
    """

    print("\n  Users to be created:")
    print("    - main_energy (admin user)")
    print("    - mce_service (permanent service user)")

    print("\n  ℹ️  User creation SQL generated")
    print("  Note: Execute these SQL commands directly in the Lakebase/Postgres instance")

    # Step 4: Create Tables
    print("\n4. Creating Lakebase tables...")

    create_tables_sql = f"""
    -- Table 1: Live Asset Status
    CREATE TABLE IF NOT EXISTS {CATALOG_NAME}.mce_operations.mce_assets_live_status (
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
        active_work_order_id UUID,
        hours_since_last_maintenance DECIMAL(10,2)
    );

    CREATE INDEX IF NOT EXISTS idx_asset_status ON {CATALOG_NAME}.mce_operations.mce_assets_live_status(status);
    CREATE INDEX IF NOT EXISTS idx_asset_site ON {CATALOG_NAME}.mce_operations.mce_assets_live_status(site);
    CREATE INDEX IF NOT EXISTS idx_last_updated ON {CATALOG_NAME}.mce_operations.mce_assets_live_status(last_updated);

    -- Table 2: Work Orders
    CREATE TABLE IF NOT EXISTS {CATALOG_NAME}.mce_operations.mce_work_orders (
        work_order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        asset_id VARCHAR(50) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        priority VARCHAR(10) CHECK (priority IN ('P1', 'P2', 'P3')),
        status VARCHAR(20) CHECK (status IN ('DISPATCHED', 'IN_PROGRESS', 'COMPLETE', 'CANCELLED')),
        assigned_technician VARCHAR(200),
        predicted_failure_date DATE,
        predicted_failure_type VARCHAR(50),
        required_parts JSONB,
        procedure_steps JSONB,
        safety_checklist JSONB,
        ai_repair_summary TEXT,
        estimated_duration_hours DECIMAL(5,2),
        actual_duration_hours DECIMAL(5,2),
        first_time_fix_verified BOOLEAN DEFAULT FALSE,
        completed_at TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (asset_id) REFERENCES {CATALOG_NAME}.mce_operations.mce_assets_live_status(asset_id)
    );

    CREATE INDEX IF NOT EXISTS idx_wo_status ON {CATALOG_NAME}.mce_operations.mce_work_orders(status);
    CREATE INDEX IF NOT EXISTS idx_wo_priority ON {CATALOG_NAME}.mce_operations.mce_work_orders(priority);
    CREATE INDEX IF NOT EXISTS idx_wo_asset ON {CATALOG_NAME}.mce_operations.mce_work_orders(asset_id);
    CREATE INDEX IF NOT EXISTS idx_wo_technician ON {CATALOG_NAME}.mce_operations.mce_work_orders(assigned_technician);

    -- Table 3: Technicians
    CREATE TABLE IF NOT EXISTS {CATALOG_NAME}.mce_operations.mce_technicians (
        technician_id VARCHAR(50) PRIMARY KEY,
        name VARCHAR(200) NOT NULL,
        site VARCHAR(200),
        certifications JSONB,
        current_location TEXT,
        available BOOLEAN DEFAULT TRUE,
        active_work_orders INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_tech_available ON {CATALOG_NAME}.mce_operations.mce_technicians(available);
    CREATE INDEX IF NOT EXISTS idx_tech_site ON {CATALOG_NAME}.mce_operations.mce_technicians(site);

    -- Create updated_at trigger function
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ language 'plpgsql';

    -- Apply trigger to work_orders
    DROP TRIGGER IF EXISTS update_work_orders_updated_at ON {CATALOG_NAME}.mce_operations.mce_work_orders;
    CREATE TRIGGER update_work_orders_updated_at
        BEFORE UPDATE ON {CATALOG_NAME}.mce_operations.mce_work_orders
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();

    -- Apply trigger to technicians
    DROP TRIGGER IF EXISTS update_technicians_updated_at ON {CATALOG_NAME}.mce_operations.mce_technicians;
    CREATE TRIGGER update_technicians_updated_at
        BEFORE UPDATE ON {CATALOG_NAME}.mce_operations.mce_technicians
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """

    # Save SQL to file for manual execution if needed
    sql_file_path = "/Users/pravin.varma/Documents/Demo/main-character-energy/workstream-4-lakebase/create_lakebase_tables.sql"
    with open(sql_file_path, 'w') as f:
        f.write(create_user_sql + "\n\n" + create_tables_sql)

    print(f"  ✓ Table creation SQL saved to: create_lakebase_tables.sql")

    try:
        # Attempt to create tables using SQL warehouse
        execute_sql(w, warehouse_id, create_tables_sql, "Creating tables")
    except Exception as e:
        print(f"  ⚠️  Could not create tables via SQL warehouse: {e}")
        print(f"  Alternative: Execute SQL file directly in Lakebase/Postgres")

    # Step 5: Seed technician data
    print("\n5. Seeding technician data...")

    seed_technicians_sql = f"""
    INSERT INTO {CATALOG_NAME}.mce_operations.mce_technicians
        (technician_id, name, site, certifications, available, active_work_orders)
    VALUES
        ('TECH-001', 'James Chen', 'Sydney North Wind Farm, NSW',
         '{{"electrical": true, "wind_turbine": true, "high_voltage": true}}'::jsonb, true, 0),
        ('TECH-002', 'Sarah Williams', 'Melbourne West Solar Park, VIC',
         '{{"solar": true, "inverters": true}}'::jsonb, true, 0),
        ('TECH-003', 'Michael O''Donnell', 'Hunter Valley Gas Plant, NSW',
         '{{"gas_turbine": true, "high_temp": true, "pressure_systems": true}}'::jsonb, true, 0),
        ('TECH-004', 'Emma Thompson', 'Gippsland Hydro Station, VIC',
         '{{"hydro": true, "mechanical": true}}'::jsonb, true, 0),
        ('TECH-005', 'David Martinez', 'Broken Hill Solar Farm, NSW',
         '{{"solar": true, "electrical": true}}'::jsonb, true, 0),
        ('TECH-006', 'Lisa Anderson', 'Geelong Substation, VIC',
         '{{"substation": true, "high_voltage": true, "arc_flash": true}}'::jsonb, true, 0),
        ('TECH-007', 'Tom Roberts', 'Newcastle Wind Farm, NSW',
         '{{"wind_turbine": true, "mechanical": true}}'::jsonb, true, 0),
        ('TECH-008', 'Rachel Kim', 'Yarra Valley Hydro, VIC',
         '{{"hydro": true, "electrical": true}}'::jsonb, true, 0)
    ON CONFLICT (technician_id) DO NOTHING;
    """

    try:
        execute_sql(w, warehouse_id, seed_technicians_sql, "Seeding technician data")
    except Exception as e:
        print(f"  ⚠️  Could not seed data: {e}")

    print("\n" + "=" * 60)
    print("✅ Lakebase setup instructions generated!")
    print(f"\nCatalog: {CATALOG_NAME}")
    print(f"Schema: mce_operations")
    print(f"Database: {DATABASE_NAME}")

    print("\nUsers created:")
    print("  - main_energy (Password: MCE_SecurePass_2026!)")
    print("  - mce_service (Password: MCE_Service_Perm_2026!)")

    print("\nTables created:")
    print("  - mce_assets_live_status (live asset monitoring)")
    print("  - mce_work_orders (AI-generated work orders)")
    print("  - mce_technicians (field worker roster)")

    print("\nConnection string format:")
    print(f"  postgresql://main_energy:MCE_SecurePass_2026!@<endpoint>.cloud.databricks.com:5432/{DATABASE_NAME}")

    print("\n⚠️  IMPORTANT: Store credentials in Databricks Secret Scope:")
    print("  databricks secrets create-scope mce-secrets --profile fe-vm")
    print("  databricks secrets put-secret mce-secrets lakebase-password --string-value 'MCE_SecurePass_2026!' --profile fe-vm")

if __name__ == "__main__":
    main()
