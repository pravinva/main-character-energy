#!/usr/bin/env python3
"""
Create Lakebase catalog using Databricks SDK
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import CatalogType, CatalogInfo
import time

PROFILE = "fe-vm"
CATALOG_NAME = "mce_lakebase_catalog"

def main():
    w = WorkspaceClient(profile=PROFILE)

    print("Creating Lakebase catalog...")
    print(f"Catalog name: {CATALOG_NAME}")

    try:
        # Create Lakebase catalog using SDK
        catalog = w.catalogs.create(
            name=CATALOG_NAME,
            comment="Main Character Energy - Lakebase Serverless Postgres",
            catalog_type=CatalogType.SYSTEM,  # Try SYSTEM type
            properties={
                "type": "POSTGRES",
                "project": "mce_operations",
                "branch": "main"
            }
        )

        print(f"✓ Catalog created: {catalog.name}")
        print(f"  Type: {catalog.catalog_type}")
        print(f"  Full name: {catalog.full_name}")

        # Wait for provisioning
        print("\nWaiting for provisioning (this takes 3-5 minutes)...")
        time.sleep(10)

        # Check status
        catalog_info = w.catalogs.get(name=CATALOG_NAME)
        print(f"\n✓ Catalog status: {catalog_info}")

    except Exception as e:
        print(f"✗ Error creating catalog: {e}")
        print(f"\nNote: Lakebase catalogs may require manual creation via UI")
        print(f"UI Path: Catalog Explorer → + Add Catalog → lakebase_postgres")
        print(f"Required fields:")
        print(f"  - Catalog name: {CATALOG_NAME}")
        print(f"  - Project: mce_operations")
        print(f"  - Branch: main")

if __name__ == "__main__":
    main()
