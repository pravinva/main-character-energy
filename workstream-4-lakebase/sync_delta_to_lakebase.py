#!/usr/bin/env python3
"""
Main Character Energy - Delta to Lakebase Sync Pipeline
Syncs critical alerts from Delta tables to Lakebase (Serverless Postgres)

Runs every 30 seconds to ensure real-time mobile app responsiveness
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import psycopg2
from psycopg2 import pool
import time
import json
from datetime import datetime

# Configuration
CATALOG = "serverless_sandbox_tladem_catalog"
DELTA_TABLE = f"{CATALOG}.mce_silver.critical_alerts"
LAKEBASE_CATALOG = "mce_lakebase_catalog"
LAKEBASE_TABLE = f"{LAKEBASE_CATALOG}.mce_operations.mce_assets_live_status"
WAREHOUSE_ID = "a62624c51dced859"

# Lakebase connection (using service account created by create_tables_direct.py)
# In production: fetch from Databricks Secrets
LAKEBASE_CONN_STRING = "postgresql://mce_service:MCE_Service_2026!@ep-tiny-field-d2xsbyci.database.us-east-1.cloud.databricks.com:5432/databricks_postgres?sslmode=require"

# Sync interval
SYNC_INTERVAL_SECONDS = 30

class DeltaToLakebaseSync:
    def __init__(self):
        self.w = WorkspaceClient(profile="fe-vm")
        self.connection_pool = None
        self.last_sync_timestamp = None

    def init_connection_pool(self):
        """Initialize psycopg2 connection pool to Lakebase"""
        print("Initializing Lakebase connection pool...")
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=2,
                maxconn=10,
                dsn=LAKEBASE_CONN_STRING
            )
            print("  ✓ Connection pool created")
        except Exception as e:
            print(f"  ✗ Failed to create connection pool: {e}")
            raise

    def get_connection(self):
        """Get connection from pool"""
        return self.connection_pool.getconn()

    def return_connection(self, conn):
        """Return connection to pool"""
        self.connection_pool.putconn(conn)

    def fetch_critical_alerts(self):
        """Fetch new/updated critical alerts from Delta table"""
        print(f"\nFetching critical alerts from Delta table...")

        # Build query with timestamp filter for incremental updates
        query = f"""
        SELECT
            asset_id,
            asset_name,
            site,
            asset_type,
            vibration_hz,
            temp_celsius,
            rpm,
            voltage_output,
            overall_status as status,
            predicted_failure_type,
            hours_since_last_maintenance,
            processed_timestamp as last_updated
        FROM {DELTA_TABLE}
        """

        if self.last_sync_timestamp:
            query += f" WHERE processed_timestamp > '{self.last_sync_timestamp}'"

        query += " ORDER BY processed_timestamp DESC"

        try:
            statement = self.w.statement_execution.execute_statement(
                warehouse_id=WAREHOUSE_ID,
                statement=query,
                wait_timeout="50s"
            )

            while statement.status.state in [StatementState.PENDING, StatementState.RUNNING]:
                time.sleep(1)
                statement = self.w.statement_execution.get_statement(statement.statement_id)

            if statement.status.state == StatementState.SUCCEEDED:
                if statement.result and statement.result.data_array:
                    rows = statement.result.data_array
                    print(f"  ✓ Fetched {len(rows)} critical alerts")
                    return rows
                else:
                    print("  ℹ️  No new critical alerts")
                    return []
            else:
                error_msg = statement.status.error.message if statement.status.error else "Unknown error"
                print(f"  ✗ Query failed: {error_msg}")
                return []

        except Exception as e:
            print(f"  ✗ Error fetching alerts: {e}")
            return []

    def upsert_to_lakebase(self, alerts):
        """UPSERT alerts into Lakebase"""
        if not alerts:
            return

        print(f"\nUpserting {len(alerts)} alerts to Lakebase...")

        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # UPSERT using INSERT ... ON CONFLICT (Postgres)
            upsert_query = """
            INSERT INTO mce_operations.mce_assets_live_status
                (asset_id, asset_name, site, asset_type, vibration_hz, temp_celsius,
                 rpm, voltage_output, status, predicted_failure_type,
                 hours_since_last_maintenance, last_updated)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (asset_id)
            DO UPDATE SET
                asset_name = EXCLUDED.asset_name,
                site = EXCLUDED.site,
                asset_type = EXCLUDED.asset_type,
                vibration_hz = EXCLUDED.vibration_hz,
                temp_celsius = EXCLUDED.temp_celsius,
                rpm = EXCLUDED.rpm,
                voltage_output = EXCLUDED.voltage_output,
                status = EXCLUDED.status,
                predicted_failure_type = EXCLUDED.predicted_failure_type,
                hours_since_last_maintenance = EXCLUDED.hours_since_last_maintenance,
                last_updated = EXCLUDED.last_updated
            """

            upserted_count = 0
            for alert in alerts:
                try:
                    cursor.execute(upsert_query, (
                        alert[0],   # asset_id
                        alert[1],   # asset_name
                        alert[2],   # site
                        alert[3],   # asset_type
                        float(alert[4]) if alert[4] else None,  # vibration_hz
                        float(alert[5]) if alert[5] else None,  # temp_celsius
                        float(alert[6]) if alert[6] else None,  # rpm
                        float(alert[7]) if alert[7] else None,  # voltage_output
                        alert[8],   # status
                        alert[9],   # predicted_failure_type
                        float(alert[10]) if alert[10] else None,  # hours_since_last_maintenance
                        alert[11]   # last_updated
                    ))
                    upserted_count += 1
                except Exception as e:
                    print(f"  ⚠️  Error upserting asset {alert[0]}: {e}")
                    continue

            conn.commit()
            cursor.close()

            print(f"  ✓ Upserted {upserted_count}/{len(alerts)} assets")

        except Exception as e:
            print(f"  ✗ Error in upsert: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                self.return_connection(conn)

    def sync_once(self):
        """Perform one sync iteration"""
        print("\n" + "=" * 60)
        print(f"Sync iteration at {datetime.now().isoformat()}")

        # Fetch new/updated alerts
        alerts = self.fetch_critical_alerts()

        # Upsert to Lakebase
        if alerts:
            self.upsert_to_lakebase(alerts)

            # Update last sync timestamp
            max_timestamp = max(alert[11] for alert in alerts if alert[11])
            self.last_sync_timestamp = max_timestamp
            print(f"\n  Last sync timestamp: {self.last_sync_timestamp}")
        else:
            print("\n  No updates to sync")

    def run_continuous(self):
        """Run continuous sync loop"""
        print("Main Character Energy - Delta to Lakebase Sync")
        print("=" * 60)
        print(f"Source: {DELTA_TABLE}")
        print(f"Target: {LAKEBASE_TABLE}")
        print(f"Interval: {SYNC_INTERVAL_SECONDS} seconds")

        # Initialize connection pool
        self.init_connection_pool()

        print("\nStarting continuous sync loop...")
        print("Press Ctrl+C to stop")

        try:
            while True:
                try:
                    self.sync_once()
                except Exception as e:
                    print(f"\n✗ Sync iteration failed: {e}")
                    print("  Retrying in next iteration...")

                time.sleep(SYNC_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            print("\n\nStopping sync pipeline...")
        finally:
            if self.connection_pool:
                self.connection_pool.closeall()
                print("Connection pool closed")

def main():
    syncer = DeltaToLakebaseSync()
    syncer.run_continuous()

if __name__ == "__main__":
    main()
