#!/usr/bin/env python3
"""
Main Character Energy - Unity Catalog Setup Script
Provisions catalog, schemas, and volumes for the field operations platform
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import VolumeType
import time

def setup_catalog():
    """Create Unity Catalog structure for Main Character Energy"""

    # Initialize workspace client (uses fe-vm profile from environment)
    w = WorkspaceClient(profile="fe-vm")

    print("🏗️  Setting up Unity Catalog for Main Character Energy...")

    # Create catalog
    print("\n1. Creating catalog: field_operations_mce")
    try:
        w.catalogs.create(
            name="field_operations_mce",
            comment="Main Character Energy - Agentic Field Management Platform"
        )
        print("   ✓ Catalog created")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("   ℹ️  Catalog already exists")
        else:
            print(f"   ✗ Error: {e}")
            raise

    # Wait a moment for catalog to be ready
    time.sleep(2)

    # Create schemas
    schemas = {
        "raw": "Raw ingestion layer - sensor data, manuals, checklists",
        "silver": "Cleaned and enriched data layer",
        "gold": "Business-level aggregated metrics",
        "agents": "Agent tools, vector indexes, and AI artifacts",
        "lakebase_sync": "Staging tables for Lakebase synchronization"
    }

    print("\n2. Creating schemas...")
    for schema_name, comment in schemas.items():
        try:
            w.schemas.create(
                name=schema_name,
                catalog_name="field_operations_mce",
                comment=comment
            )
            print(f"   ✓ Schema created: {schema_name}")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"   ℹ️  Schema already exists: {schema_name}")
            else:
                print(f"   ✗ Error creating {schema_name}: {e}")
                raise

    # Wait for schemas to be ready
    time.sleep(2)

    # Create volumes
    volumes = {
        "telemetry_ingest": "Incoming sensor telemetry CSV/JSON files",
        "technical_manuals": "PDF repair manuals and technical documentation",
        "safety_checklists": "Safety procedure checklists and compliance documents"
    }

    print("\n3. Creating volumes in raw schema...")
    for volume_name, comment in volumes.items():
        try:
            w.volumes.create(
                catalog_name="field_operations_mce",
                schema_name="raw",
                name=volume_name,
                volume_type=VolumeType.MANAGED,
                comment=comment
            )
            print(f"   ✓ Volume created: {volume_name}")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"   ℹ️  Volume already exists: {volume_name}")
            else:
                print(f"   ✗ Error creating {volume_name}: {e}")
                raise

    print("\n✅ Unity Catalog setup complete!")
    print("\nCatalog structure:")
    print("field_operations_mce/")
    print("├── raw/")
    print("│   ├── telemetry_ingest (volume)")
    print("│   ├── technical_manuals (volume)")
    print("│   └── safety_checklists (volume)")
    print("├── silver/")
    print("├── gold/")
    print("├── agents/")
    print("└── lakebase_sync/")

    # Verify volumes exist and get paths
    print("\n4. Verifying volume paths...")
    for volume_name in volumes.keys():
        try:
            volume_info = w.volumes.read(
                full_name_arg=f"field_operations_mce.raw.{volume_name}"
            )
            print(f"   ✓ {volume_name}: {volume_info.volume_path}")
        except Exception as e:
            print(f"   ✗ Error reading {volume_name}: {e}")

if __name__ == "__main__":
    setup_catalog()
