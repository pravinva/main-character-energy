#!/usr/bin/env python3
"""
Validate Main Character Energy - Workstream 1 Foundation Setup
Checks catalog structure, volumes, and data quality
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import time

CATALOG_NAME = "serverless_sandbox_tladem_catalog"
WAREHOUSE_ID = "a62624c51dced859"

def execute_sql(w, sql_statement):
    """Execute SQL and return results"""
    statement = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=sql_statement,
        wait_timeout="50s"
    )

    while statement.status.state in [StatementState.PENDING, StatementState.RUNNING]:
        time.sleep(1)
        statement = w.statement_execution.get_statement(statement.statement_id)

    if statement.status.state == StatementState.SUCCEEDED:
        return statement.result
    else:
        raise Exception(f"SQL failed: {statement.status.error}")

def main():
    w = WorkspaceClient(profile="fe-vm")

    print("Main Character Energy - Foundation Validation")
    print("=" * 60)

    # Check schemas
    print("\n1. Verifying schemas...")
    result = execute_sql(w, f"SHOW SCHEMAS IN {CATALOG_NAME}")
    schemas = [row[0] for row in result.data_array if 'mce_' in str(row[0]).lower()]
    expected_schemas = ['mce_raw', 'mce_silver', 'mce_gold', 'mce_agents', 'mce_lakebase']

    for schema in expected_schemas:
        if schema in schemas:
            print(f"  ✓ {schema}")
        else:
            print(f"  ✗ {schema} - MISSING!")

    # Check volumes
    print("\n2. Verifying volumes...")
    result = execute_sql(w, f"SHOW VOLUMES IN {CATALOG_NAME}.mce_raw")
    # Extract volume names from result (usually in column 0 or 1)
    volume_names = [str(row[0]).lower() if row else '' for row in result.data_array]
    expected_volumes = ['telemetry_ingest', 'technical_manuals', 'safety_checklists']

    for vol in expected_volumes:
        if any(vol in vname for vname in volume_names):
            print(f"  ✓ {vol}")
        else:
            print(f"  ✗ {vol} - MISSING!")

    # Check files in volumes
    print("\n3. Checking uploaded files...")
    print("  Telemetry Ingest Volume:")
    telemetry_files = execute_sql(w, f"LIST '/Volumes/{CATALOG_NAME}/mce_raw/telemetry_ingest/'")
    if telemetry_files.data_array:
        for row in telemetry_files.data_array:
            filename = row[0].split('/')[-1]
            print(f"    ✓ {filename}")
    else:
        print("    ✗ No files found!")

    print("  Technical Manuals Volume:")
    manual_files = execute_sql(w, f"LIST '/Volumes/{CATALOG_NAME}/mce_raw/technical_manuals/'")
    if manual_files.data_array:
        for row in manual_files.data_array:
            filename = row[0].split('/')[-1]
            print(f"    ✓ {filename}")
    else:
        print("    ✗ No files found!")

    # Create Delta tables from uploaded data
    print("\n4. Creating Delta tables from raw data...")

    # Sensor telemetry table
    execute_sql(w, f"""
        CREATE TABLE IF NOT EXISTS {CATALOG_NAME}.mce_raw.sensor_telemetry
        USING CSV
        OPTIONS (header='true', inferSchema='true')
        LOCATION '/Volumes/{CATALOG_NAME}/mce_raw/telemetry_ingest/sensor_telemetry.csv'
    """)
    print("  ✓ sensor_telemetry table created")

    # Asset registry table
    execute_sql(w, f"""
        CREATE TABLE IF NOT EXISTS {CATALOG_NAME}.mce_raw.asset_registry
        USING JSON
        LOCATION '/Volumes/{CATALOG_NAME}/mce_raw/telemetry_ingest/asset_registry.json'
    """)
    print("  ✓ asset_registry table created")

    # Maintenance history table
    execute_sql(w, f"""
        CREATE TABLE IF NOT EXISTS {CATALOG_NAME}.mce_raw.maintenance_history
        USING PARQUET
        LOCATION '/Volumes/{CATALOG_NAME}/mce_raw/telemetry_ingest/maintenance_history.parquet'
    """)
    print("  ✓ maintenance_history table created")

    # Data quality checks
    print("\n5. Data quality validation...")

    # Check sensor telemetry
    result = execute_sql(w, f"SELECT COUNT(*) as count FROM {CATALOG_NAME}.mce_raw.sensor_telemetry")
    telemetry_count = result.data_array[0][0]
    print(f"  ✓ Sensor telemetry: {telemetry_count} records")

    result = execute_sql(w, f"SELECT COUNT(*) FROM {CATALOG_NAME}.mce_raw.sensor_telemetry WHERE vibration_hz > 80")
    critical_count = result.data_array[0][0]
    print(f"  ✓ CRITICAL assets (vibration > 80Hz): {critical_count}")

    result = execute_sql(w, f"SELECT COUNT(*) FROM {CATALOG_NAME}.mce_raw.sensor_telemetry WHERE vibration_hz BETWEEN 60 AND 80")
    warning_count = result.data_array[0][0]
    print(f"  ✓ WARNING assets (vibration 60-80Hz): {warning_count}")

    # Check asset registry
    result = execute_sql(w, f"SELECT COUNT(*) FROM {CATALOG_NAME}.mce_raw.asset_registry")
    asset_count = result.data_array[0][0]
    print(f"  ✓ Asset registry: {asset_count} assets")

    # Check maintenance history
    result = execute_sql(w, f"SELECT COUNT(*) FROM {CATALOG_NAME}.mce_raw.maintenance_history")
    maint_count = result.data_array[0][0]
    print(f"  ✓ Maintenance history: {maint_count} events")

    print("\n" + "=" * 60)
    print("✅ Workstream 1 - Foundation validation complete!")
    print(f"\nCatalog: {CATALOG_NAME}")
    print("Status: READY for Workstream 2 (Lakeflow Ingestion)")

if __name__ == "__main__":
    main()
