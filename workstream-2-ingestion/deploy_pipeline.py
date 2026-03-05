#!/usr/bin/env python3
"""
Deploy Main Character Energy DLT Pipeline
Uploads notebook, creates pipeline, and triggers initial run
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.pipelines import *
from databricks.sdk.service.workspace import ImportFormat, Language
import json
import time
import base64

PROFILE = "fe-vm"
WORKSPACE_PATH = "/Users/pravin.varma@databricks.com/main-character-energy"
PIPELINE_NAME = "mce_telemetry_ingestion"
CATALOG = "serverless_sandbox_tladem_catalog"
TARGET_SCHEMA = "mce_silver"

def main():
    w = WorkspaceClient(profile=PROFILE)

    print("Main Character Energy - DLT Pipeline Deployment")
    print("=" * 60)

    # Step 1: Upload DLT notebook
    print("\n1. Uploading DLT pipeline notebook...")
    notebook_path = f"{WORKSPACE_PATH}/mce_dlt_pipeline"

    try:
        with open("mce_dlt_pipeline.py", "r") as f:
            notebook_content = f.read()

        # Convert to base64 for upload
        encoded_content = base64.b64encode(notebook_content.encode()).decode()

        w.workspace.import_(
            path=notebook_path,
            format=ImportFormat.SOURCE,
            language=Language.PYTHON,
            content=encoded_content,
            overwrite=True
        )
        print(f"  ✓ Notebook uploaded to: {notebook_path}")
    except Exception as e:
        print(f"  ✗ Error uploading notebook: {e}")
        return

    # Step 2: Check if pipeline exists
    print("\n2. Checking for existing pipeline...")
    existing_pipeline = None
    try:
        pipelines = w.pipelines.list_pipelines()
        for p in pipelines:
            if p.name == PIPELINE_NAME:
                existing_pipeline = p
                print(f"  ℹ️  Found existing pipeline: {p.pipeline_id}")
                break

        if not existing_pipeline:
            print("  ℹ️  No existing pipeline found, will create new one")
    except Exception as e:
        print(f"  ⚠️  Could not list pipelines: {e}")

    # Step 3: Create or update pipeline
    print("\n3. Creating/updating DLT pipeline...")

    pipeline_spec = PipelineSpec(
        name=PIPELINE_NAME,
        catalog=CATALOG,  # Required for serverless
        storage=f"dbfs:/pipelines/mce_telemetry",
        configuration={
            "pipelines.applyChangesPreviewEnabled": "true"
        },
        serverless=True,  # Use serverless compute
        libraries=[
            PipelineLibrary(
                notebook=NotebookLibrary(path=notebook_path)
            )
        ],
        target=f"{CATALOG}.{TARGET_SCHEMA}",
        continuous=False,
        channel="CURRENT",
        photon=True,
        edition="ADVANCED"
    )

    try:
        if existing_pipeline:
            # Update existing pipeline
            w.pipelines.update(
                pipeline_id=existing_pipeline.pipeline_id,
                name=pipeline_spec.name,
                catalog=pipeline_spec.catalog,
                storage=pipeline_spec.storage,
                configuration=pipeline_spec.configuration,
                serverless=pipeline_spec.serverless,
                libraries=pipeline_spec.libraries,
                target=pipeline_spec.target,
                continuous=pipeline_spec.continuous,
                channel=pipeline_spec.channel,
                photon=pipeline_spec.photon,
                edition=pipeline_spec.edition
            )
            pipeline_id = existing_pipeline.pipeline_id
            print(f"  ✓ Pipeline updated: {pipeline_id}")
        else:
            # Create new pipeline
            created = w.pipelines.create(
                name=pipeline_spec.name,
                catalog=pipeline_spec.catalog,
                storage=pipeline_spec.storage,
                configuration=pipeline_spec.configuration,
                serverless=pipeline_spec.serverless,
                libraries=pipeline_spec.libraries,
                target=pipeline_spec.target,
                continuous=pipeline_spec.continuous,
                channel=pipeline_spec.channel,
                photon=pipeline_spec.photon,
                edition=pipeline_spec.edition
            )
            pipeline_id = created.pipeline_id
            print(f"  ✓ Pipeline created: {pipeline_id}")

    except Exception as e:
        print(f"  ✗ Error creating/updating pipeline: {e}")
        return

    # Step 4: Trigger pipeline run
    print("\n4. Starting pipeline update (full refresh)...")
    try:
        update = w.pipelines.start_update(
            pipeline_id=pipeline_id,
            full_refresh=True
        )
        update_id = update.update_id
        print(f"  ✓ Pipeline update started: {update_id}")
        print(f"  📊 Monitor at: https://fe-sandbox-serverless-sandbox-tladem.cloud.databricks.com/#joblist/pipelines/{pipeline_id}")

    except Exception as e:
        print(f"  ✗ Error starting pipeline: {e}")
        return

    # Step 5: Monitor pipeline progress
    print("\n5. Monitoring pipeline progress...")
    print("  (This may take 5-10 minutes for initial run)")

    max_wait = 1800  # 30 minutes
    start_time = time.time()

    while time.time() - start_time < max_wait:
        try:
            update_info = w.pipelines.get_update(
                pipeline_id=pipeline_id,
                update_id=update_id
            )

            state = update_info.update.state
            print(f"  Status: {state}", end="\r")

            if state in ["COMPLETED", "FAILED", "CANCELED"]:
                print(f"\n  Pipeline finished with state: {state}")

                if state == "COMPLETED":
                    print("\n✅ Pipeline execution successful!")

                    # Query results
                    print("\n6. Validating pipeline outputs...")
                    try:
                        from databricks.sdk.service.sql import StatementState

                        warehouse_id = "a62624c51dced859"

                        # Check critical alerts
                        stmt = w.statement_execution.execute_statement(
                            warehouse_id=warehouse_id,
                            statement=f"SELECT COUNT(*) as count FROM {CATALOG}.{TARGET_SCHEMA}.critical_alerts",
                            wait_timeout="30s"
                        )

                        while stmt.status.state in [StatementState.PENDING, StatementState.RUNNING]:
                            time.sleep(1)
                            stmt = w.statement_execution.get_statement(stmt.statement_id)

                        if stmt.status.state == StatementState.SUCCEEDED and stmt.result.data_array:
                            critical_count = stmt.result.data_array[0][0]
                            print(f"  ✓ Critical alerts table: {critical_count} records")

                        # Check silver telemetry
                        stmt = w.statement_execution.execute_statement(
                            warehouse_id=warehouse_id,
                            statement=f"SELECT COUNT(*) FROM {CATALOG}.{TARGET_SCHEMA}.silver_asset_telemetry",
                            wait_timeout="30s"
                        )

                        while stmt.status.state in [StatementState.PENDING, StatementState.RUNNING]:
                            time.sleep(1)
                            stmt = w.statement_execution.get_statement(stmt.statement_id)

                        if stmt.status.state == StatementState.SUCCEEDED and stmt.result.data_array:
                            telemetry_count = stmt.result.data_array[0][0]
                            print(f"  ✓ Silver telemetry table: {telemetry_count} records")

                    except Exception as e:
                        print(f"  ⚠️  Could not validate outputs: {e}")

                elif state == "FAILED":
                    print("\n✗ Pipeline execution failed!")
                    print("  Check the pipeline UI for error details")

                break

            time.sleep(10)

        except Exception as e:
            print(f"\n  ⚠️  Error monitoring pipeline: {e}")
            break

    else:
        print(f"\n  ⚠️  Pipeline still running after {max_wait} seconds")
        print("  Check the UI for current status")

    print("\n" + "=" * 60)
    print("Deployment complete!")
    print(f"Pipeline ID: {pipeline_id}")
    print(f"Target: {CATALOG}.{TARGET_SCHEMA}")

if __name__ == "__main__":
    main()
