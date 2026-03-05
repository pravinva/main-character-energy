#!/usr/bin/env python3
"""
Create Lakebase tables via SQL Warehouse
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import time

PROFILE = "fe-vm"
WAREHOUSE_ID = "a62624c51dced859"
CATALOG = "mce_lakebase_catalog"
SCHEMA = "mce_operations"

def execute_sql(w, sql, description=""):
    """Execute SQL and wait for completion"""
    if description:
        print(f"  {description}...")

    try:
        statement = w.statement_execution.execute_statement(
            warehouse_id=WAREHOUSE_ID,
            statement=sql,
            wait_timeout="50s"
        )

        while statement.status.state in [StatementState.PENDING, StatementState.RUNNING]:
            time.sleep(1)
            statement = w.statement_execution.get_statement(statement.statement_id)

        if statement.status.state == StatementState.SUCCEEDED:
            print(f"    ✓ Success")
            return True
        else:
            error_msg = statement.status.error.message if statement.status.error else "Unknown error"
            print(f"    ✗ Failed: {error_msg}")
            return False
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False

def main():
    w = WorkspaceClient(profile=PROFILE)

    print("Main Character Energy - Lakebase Table Setup via SQL Warehouse")
    print("=" * 60)
    print(f"Catalog: {CATALOG}")
    print(f"Schema: {SCHEMA}")

    # Set context
    print("\n0. Setting context...")
    execute_sql(w, f"USE CATALOG {CATALOG}", "Using catalog")
    execute_sql(w, f"USE SCHEMA {SCHEMA}", "Using schema")

    # Table 1: mce_assets_live_status
    print("\n1. Creating mce_assets_live_status...")
    sql1 = f"""
    CREATE TABLE IF NOT EXISTS {CATALOG}.{SCHEMA}.mce_assets_live_status (
        asset_id STRING,
        site STRING,
        asset_type STRING,
        asset_name STRING,
        vibration_hz DECIMAL(10,2),
        temp_celsius DECIMAL(10,2),
        rpm DECIMAL(10,2),
        voltage_output DECIMAL(15,2),
        status STRING,
        predicted_failure_type STRING,
        last_updated TIMESTAMP,
        active_work_order_id STRING,
        hours_since_last_maintenance DECIMAL(10,2)
    )
    """
    execute_sql(w, sql1, "Creating table")

    # Table 2: mce_work_orders
    print("\n2. Creating mce_work_orders...")
    sql2 = f"""
    CREATE TABLE IF NOT EXISTS {CATALOG}.{SCHEMA}.mce_work_orders (
        work_order_id STRING,
        asset_id STRING,
        created_at TIMESTAMP,
        priority STRING,
        status STRING,
        assigned_technician STRING,
        predicted_failure_date DATE,
        predicted_failure_type STRING,
        required_parts STRING,
        procedure_steps STRING,
        safety_checklist STRING,
        ai_repair_summary STRING,
        estimated_duration_hours DECIMAL(5,2),
        actual_duration_hours DECIMAL(5,2),
        first_time_fix_verified BOOLEAN,
        completed_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    """
    execute_sql(w, sql2, "Creating table")

    # Table 3: mce_technicians
    print("\n3. Creating mce_technicians...")
    sql3 = f"""
    CREATE TABLE IF NOT EXISTS {CATALOG}.{SCHEMA}.mce_technicians (
        technician_id STRING,
        name STRING,
        site STRING,
        certifications STRING,
        current_location STRING,
        available BOOLEAN,
        active_work_orders INT,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    """
    execute_sql(w, sql3, "Creating table")

    # Seed technicians
    print("\n4. Seeding technician data...")
    seed_sql = f"""
    INSERT INTO {CATALOG}.{SCHEMA}.mce_technicians
        (technician_id, name, site, certifications, available, active_work_orders, created_at)
    VALUES
        ('TECH-001', 'James Chen', 'Sydney North Wind Farm, NSW',
         '{{"electrical": true, "wind_turbine": true, "high_voltage": true}}', true, 0, current_timestamp()),
        ('TECH-002', 'Sarah Williams', 'Melbourne West Solar Park, VIC',
         '{{"solar": true, "inverters": true}}', true, 0, current_timestamp()),
        ('TECH-003', 'Michael ODonnell', 'Hunter Valley Gas Plant, NSW',
         '{{"gas_turbine": true, "high_temp": true, "pressure_systems": true}}', true, 0, current_timestamp()),
        ('TECH-004', 'Emma Thompson', 'Gippsland Hydro Station, VIC',
         '{{"hydro": true, "mechanical": true}}', true, 0, current_timestamp()),
        ('TECH-005', 'David Martinez', 'Broken Hill Solar Farm, NSW',
         '{{"solar": true, "electrical": true}}', true, 0, current_timestamp()),
        ('TECH-006', 'Lisa Anderson', 'Geelong Substation, VIC',
         '{{"substation": true, "high_voltage": true, "arc_flash": true}}', true, 0, current_timestamp()),
        ('TECH-007', 'Tom Roberts', 'Newcastle Wind Farm, NSW',
         '{{"wind_turbine": true, "mechanical": true}}', true, 0, current_timestamp()),
        ('TECH-008', 'Rachel Kim', 'Yarra Valley Hydro, VIC',
         '{{"hydro": true, "electrical": true}}', true, 0, current_timestamp())
    """

    execute_sql(w, seed_sql, "Inserting technicians")

    print("\n" + "=" * 60)
    print("✅ Lakebase tables created successfully!")
    print(f"\nTables in {CATALOG}.{SCHEMA}:")
    print("  - mce_assets_live_status")
    print("  - mce_work_orders")
    print("  - mce_technicians")

if __name__ == "__main__":
    main()
