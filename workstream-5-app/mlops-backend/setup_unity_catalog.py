"""
Unity Catalog Setup for Main Character Energy Field Operations
Creates catalog, schemas, volumes, and tables for the MLOps pipeline
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import (
    VolumeType,
    TableType,
    ColumnInfo,
    DataSourceFormat
)
import os

def setup_unity_catalog():
    """Set up Unity Catalog structure for Field Operations"""

    # Initialize Databricks client
    w = WorkspaceClient()

    catalog_name = "field_operations"

    print("=" * 80)
    print("UNITY CATALOG SETUP FOR MAIN CHARACTER ENERGY")
    print("=" * 80)

    # Step 1: Create catalog
    print(f"\n[1/5] Creating catalog '{catalog_name}'...")
    try:
        w.catalogs.create(name=catalog_name, comment="Main Character Energy Field Operations MLOps Catalog")
        print(f"✓ Catalog '{catalog_name}' created")
    except Exception as e:
        if "already exists" in str(e):
            print(f"✓ Catalog '{catalog_name}' already exists")
        else:
            raise e

    # Step 2: Create schemas
    print(f"\n[2/5] Creating schemas...")
    schemas = {
        "bronze": "Raw IoT telemetry data ingested from sensors",
        "silver": "Cleaned and validated sensor data with anomaly flags",
        "gold": "Aggregated metrics and business-ready views",
        "models": "ML models and predictions",
        "agents": "AI agent outputs and work orders"
    }

    for schema_name, comment in schemas.items():
        full_schema = f"{catalog_name}.{schema_name}"
        try:
            w.schemas.create(name=schema_name, catalog_name=catalog_name, comment=comment)
            print(f"  ✓ Schema '{full_schema}' created")
        except Exception as e:
            if "already exists" in str(e):
                print(f"  ✓ Schema '{full_schema}' already exists")
            else:
                raise e

    # Step 3: Create volumes for data storage
    print(f"\n[3/5] Creating volumes...")
    volumes = {
        ("bronze", "iot_telemetry_raw"): "Raw IoT sensor telemetry files (CSV/JSON)",
        ("bronze", "technical_manuals"): "Equipment technical manuals and repair procedures (PDFs)",
        ("bronze", "safety_checklists"): "Safety compliance checklists",
        ("models", "checkpoints"): "Model training checkpoints and artifacts"
    }

    for (schema_name, volume_name), comment in volumes.items():
        full_volume = f"{catalog_name}.{schema_name}.{volume_name}"
        try:
            w.volumes.create(
                catalog_name=catalog_name,
                schema_name=schema_name,
                name=volume_name,
                volume_type=VolumeType.MANAGED,
                comment=comment
            )
            print(f"  ✓ Volume '{full_volume}' created")
        except Exception as e:
            if "already exists" in str(e):
                print(f"  ✓ Volume '{full_volume}' already exists")
            else:
                raise e

    # Step 4: Create bronze tables
    print(f"\n[4/5] Creating bronze tables (will be populated by Lakeflow pipeline)...")

    # Note: In a real implementation, we'd create external tables or
    # let Lakeflow auto-create them. For now, we'll document the schema.

    print("""
  Expected bronze tables (created by Lakeflow):
    - bronze.sensor_telemetry (timestamp, asset_id, vibration_hz, temp_celsius, pressure_bar, etc.)
    - bronze.maintenance_history (asset_id, maintenance_date, work_performed, parts_replaced, etc.)
    """)

    # Step 5: Create silver/gold tables
    print(f"\n[5/5] Creating silver and gold tables...")

    print("""
  Silver tables (created by Lakeflow):
    - silver.sensor_telemetry_clean (deduplicated, validated sensor data)
    - silver.critical_alerts (anomaly detection results, vibration > 80Hz, etc.)

  Gold tables (created by Lakeflow):
    - gold.asset_health_summary (aggregated metrics per asset)
    - gold.predictive_maintenance_scores (failure probability scores)

  Agent tables:
    - agents.work_orders_generated (AI-generated work orders)
    - agents.technical_assistant_queries (RAG queries and responses)
    """)

    print("\n" + "=" * 80)
    print("UNITY CATALOG SETUP COMPLETE")
    print("=" * 80)
    print(f"""
Next steps:
1. Upload mock data to volumes using dbfs CLI or notebook
2. Deploy Lakeflow pipeline to ingest data
3. Set up Agent Bricks framework for AI work order generation

Volume paths for data upload:
  - /Volumes/{catalog_name}/bronze/iot_telemetry_raw/
  - /Volumes/{catalog_name}/bronze/technical_manuals/
  - /Volumes/{catalog_name}/bronze/safety_checklists/
    """)

if __name__ == "__main__":
    setup_unity_catalog()
