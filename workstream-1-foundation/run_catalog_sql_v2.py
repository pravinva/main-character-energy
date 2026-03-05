#!/usr/bin/env python3
"""
Execute catalog setup SQL using existing FE-VM catalog
Uses: serverless_sandbox_tladem_catalog (pre-created FE-VM catalog)
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import time

# Use the existing FE-VM catalog instead of creating new one
CATALOG_NAME = "serverless_sandbox_tladem_catalog"

def execute_sql(w, warehouse_id, sql_statement):
    """Execute a SQL statement and wait for completion"""
    print(f"Executing: {sql_statement[:80]}...")

    statement = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql_statement,
        wait_timeout="30s"
    )

    # Wait for completion
    while statement.status.state in [StatementState.PENDING, StatementState.RUNNING]:
        time.sleep(1)
        statement = w.statement_execution.get_statement(statement.statement_id)

    if statement.status.state == StatementState.SUCCEEDED:
        print(f"  ✓ Success")
        return True
    else:
        print(f"  ✗ Failed: {statement.status.state}")
        if statement.status.error:
            print(f"    Error: {statement.status.error.message}")
        return False

def main():
    w = WorkspaceClient(profile="fe-vm")
    warehouse_id = "a62624c51dced859"  # Serverless Starter Warehouse

    print("Main Character Energy - Catalog Setup")
    print(f"Using existing catalog: {CATALOG_NAME}")
    print("=" * 60)

    # Verify catalog exists
    print("\n1. Verifying catalog exists...")
    execute_sql(w, warehouse_id, f"DESCRIBE CATALOG {CATALOG_NAME}")

    # Create schemas for Main Character Energy
    print("\n2. Creating schemas...")
    schemas = [
        ('mce_raw', 'Main Character Energy: Raw ingestion layer'),
        ('mce_silver', 'Main Character Energy: Cleaned data layer'),
        ('mce_gold', 'Main Character Energy: Business aggregates'),
        ('mce_agents', 'Main Character Energy: Agent tools and AI'),
        ('mce_lakebase', 'Main Character Energy: Lakebase sync staging')
    ]

    for schema_name, comment in schemas:
        execute_sql(w, warehouse_id, f"""
            CREATE SCHEMA IF NOT EXISTS {CATALOG_NAME}.{schema_name}
            COMMENT '{comment}'
        """)

    # Create volumes
    print("\n3. Creating volumes in mce_raw schema...")
    volumes = [
        ('telemetry_ingest', 'Incoming sensor telemetry CSV/JSON files'),
        ('technical_manuals', 'PDF repair manuals and technical documentation'),
        ('safety_checklists', 'Safety procedure checklists and compliance documents')
    ]

    for volume_name, comment in volumes:
        execute_sql(w, warehouse_id, f"""
            CREATE VOLUME IF NOT EXISTS {CATALOG_NAME}.mce_raw.{volume_name}
            COMMENT '{comment}'
        """)

    # Verify
    print("\n4. Verifying setup...")
    print("\nSchemas (filtered for MCE):")
    result = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=f"SHOW SCHEMAS IN {CATALOG_NAME}",
        wait_timeout="30s"
    )

    if result.result and result.result.data_array:
        for row in result.result.data_array:
            if 'mce_' in str(row[0]).lower():
                print(f"  - {row[0]}")

    print("\nVolumes in mce_raw schema:")
    result = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=f"SHOW VOLUMES IN {CATALOG_NAME}.mce_raw",
        wait_timeout="30s"
    )

    volume_paths = []
    if result.result and result.result.data_array:
        for row in result.result.data_array:
            volume_name = row[2] if len(row) > 2 else row[0]
            volume_path = row[3] if len(row) > 3 else None
            print(f"  - {volume_name}")
            if volume_path:
                volume_paths.append((volume_name, volume_path))

    print("\n" + "=" * 60)
    print("✅ Catalog setup complete!")
    print("\nCatalog structure:")
    print(f"{CATALOG_NAME}/")
    print("├── mce_raw/")
    print("│   ├── telemetry_ingest (volume)")
    print("│   ├── technical_manuals (volume)")
    print("│   └── safety_checklists (volume)")
    print("├── mce_silver/")
    print("├── mce_gold/")
    print("├── mce_agents/")
    print("└── mce_lakebase/")

    if volume_paths:
        print("\nVolume paths for file uploads:")
        for name, path in volume_paths:
            print(f"  {name}: {path}")

if __name__ == "__main__":
    main()
