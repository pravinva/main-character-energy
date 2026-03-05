#!/usr/bin/env python3
"""
Execute catalog setup SQL using Databricks SQL warehouse
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import time

def execute_sql(w, warehouse_id, sql_statement):
    """Execute a SQL statement and wait for completion"""
    print(f"Executing: {sql_statement[:100]}...")

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
    print("=" * 50)

    # Create catalog
    print("\n1. Creating catalog...")
    execute_sql(w, warehouse_id, """
        CREATE CATALOG IF NOT EXISTS field_operations_mce
        COMMENT 'Main Character Energy - Agentic Field Management Platform'
    """)

    # Create schemas
    print("\n2. Creating schemas...")
    schemas = [
        ('raw', 'Raw ingestion layer - sensor data, manuals, checklists'),
        ('silver', 'Cleaned and enriched data layer'),
        ('gold', 'Business-level aggregated metrics'),
        ('agents', 'Agent tools, vector indexes, and AI artifacts'),
        ('lakebase_sync', 'Staging tables for Lakebase synchronization')
    ]

    for schema_name, comment in schemas:
        execute_sql(w, warehouse_id, f"""
            CREATE SCHEMA IF NOT EXISTS field_operations_mce.{schema_name}
            COMMENT '{comment}'
        """)

    # Create volumes
    print("\n3. Creating volumes...")
    volumes = [
        ('telemetry_ingest', 'Incoming sensor telemetry CSV/JSON files'),
        ('technical_manuals', 'PDF repair manuals and technical documentation'),
        ('safety_checklists', 'Safety procedure checklists and compliance documents')
    ]

    for volume_name, comment in volumes:
        execute_sql(w, warehouse_id, f"""
            CREATE VOLUME IF NOT EXISTS field_operations_mce.raw.{volume_name}
            COMMENT '{comment}'
        """)

    # Verify
    print("\n4. Verifying setup...")
    print("\nSchemas:")
    result = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement="SHOW SCHEMAS IN field_operations_mce",
        wait_timeout="30s"
    )

    if result.result and result.result.data_array:
        for row in result.result.data_array:
            print(f"  - {row[0]}")

    print("\nVolumes in raw schema:")
    result = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement="SHOW VOLUMES IN field_operations_mce.raw",
        wait_timeout="30s"
    )

    if result.result and result.result.data_array:
        for row in result.result.data_array:
            print(f"  - {row[2]}")  # volume_name is typically 3rd column

    print("\n✅ Catalog setup complete!")

if __name__ == "__main__":
    main()
