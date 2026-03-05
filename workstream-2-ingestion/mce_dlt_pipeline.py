"""
Main Character Energy - Lakeflow DLT Pipeline
Bronze → Silver → Critical Alerts

This pipeline ingests telemetry data, detects anomalies, and generates
critical alerts for the Agent Bricks system.
"""

import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *

# Configuration
CATALOG = "serverless_sandbox_tladem_catalog"
RAW_SCHEMA = "mce_raw"
SILVER_SCHEMA = "mce_silver"

# Volume paths
TELEMETRY_VOLUME = f"/Volumes/{CATALOG}/{RAW_SCHEMA}/telemetry_ingest"

# ============================================================================
# BRONZE LAYER - Raw Ingestion with Schema Enforcement
# ============================================================================

@dlt.table(
    name="bronze_telemetry",
    comment="Bronze layer: Raw sensor telemetry with ingestion metadata",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.managed": "true"
    }
)
@dlt.expect_all_or_drop({
    "valid_asset_id": "asset_id IS NOT NULL",
    "valid_vibration": "vibration_hz BETWEEN 0 AND 500",
    "valid_temperature": "temp_celsius BETWEEN -50 AND 1000"
})
def bronze_telemetry():
    """
    Stream sensor telemetry from volume with schema enforcement.
    Drops rows that fail validation constraints.
    """
    return (
        spark.readStream
            .format("cloudFiles")
            .option("cloudFiles.format", "csv")
            .option("cloudFiles.schemaLocation", f"/tmp/mce_schema_bronze")
            .option("header", "true")
            .option("inferSchema", "true")
            .load(f"{TELEMETRY_VOLUME}/sensor_telemetry.csv")
            .withColumn("_ingest_timestamp", F.current_timestamp())
            .withColumn("_source_file", F.input_file_name())
    )


@dlt.table(
    name="bronze_asset_registry",
    comment="Bronze layer: Master asset registry from JSON",
    table_properties={
        "quality": "bronze"
    }
)
def bronze_asset_registry():
    """
    Load asset registry (batch - master data doesn't stream)
    """
    return (
        spark.read
            .format("json")
            .load(f"{TELEMETRY_VOLUME}/asset_registry.json")
    )


@dlt.table(
    name="bronze_maintenance_history",
    comment="Bronze layer: Historical maintenance events",
    table_properties={
        "quality": "bronze"
    }
)
def bronze_maintenance_history():
    """
    Load maintenance history (batch)
    """
    return (
        spark.read
            .format("parquet")
            .load(f"{TELEMETRY_VOLUME}/maintenance_history.parquet")
    )


# ============================================================================
# SILVER LAYER - Cleaned, Enriched, Anomaly Detection
# ============================================================================

@dlt.table(
    name="silver_asset_telemetry",
    comment="Silver layer: Cleaned telemetry joined with asset registry and enriched with anomaly flags",
    table_properties={
        "quality": "silver",
        "delta.enableChangeDataFeed": "true"
    }
)
@dlt.expect_all({
    "no_nulls_asset_id": "asset_id IS NOT NULL",
    "join_successful": "model IS NOT NULL"
})
def silver_asset_telemetry():
    """
    Join telemetry with asset registry, add anomaly detection flags,
    calculate hours since last maintenance.
    """
    telemetry = dlt.read_stream("bronze_telemetry")
    registry = dlt.read("bronze_asset_registry")
    maintenance = dlt.read("bronze_maintenance_history")

    # Get most recent maintenance per asset
    latest_maintenance = (
        maintenance
        .groupBy("asset_id")
        .agg(F.max("event_date").alias("last_maintenance_date"))
    )

    # Join telemetry with registry and maintenance
    enriched = (
        telemetry
        .join(registry, "asset_id", "left")
        .join(latest_maintenance, "asset_id", "left")
        .withColumn(
            "hours_since_last_maintenance",
            F.when(
                F.col("last_maintenance_date").isNotNull(),
                F.round(
                    (F.unix_timestamp("timestamp") - F.unix_timestamp("last_maintenance_date")) / 3600,
                    2
                )
            ).otherwise(None)
        )
        # Anomaly detection flags
        .withColumn(
            "vibration_anomaly",
            F.when(F.col("vibration_hz") > 80, F.lit("CRITICAL"))
             .when(F.col("vibration_hz") > 60, F.lit("WARNING"))
             .otherwise(F.lit("NORMAL"))
        )
        .withColumn(
            "temperature_anomaly",
            F.when(
                (F.col("asset_type") == "wind_turbine") & (F.col("temp_celsius") > 70),
                F.lit("CRITICAL")
            )
            .when(
                (F.col("asset_type") == "gas_turbine") & (F.col("temp_celsius") > 480),
                F.lit("CRITICAL")
            )
            .when(F.col("temp_celsius") > 100, F.lit("WARNING"))
            .otherwise(F.lit("NORMAL"))
        )
        .withColumn(
            "overall_status",
            F.when(
                (F.col("vibration_anomaly") == "CRITICAL") | (F.col("temperature_anomaly") == "CRITICAL"),
                F.lit("CRITICAL")
            )
            .when(
                (F.col("vibration_anomaly") == "WARNING") | (F.col("temperature_anomaly") == "WARNING"),
                F.lit("WARNING")
            )
            .otherwise(F.lit("HEALTHY"))
        )
        .withColumn("processed_timestamp", F.current_timestamp())
    )

    return enriched


@dlt.table(
    name="critical_alerts",
    comment="Silver layer: Filtered view of CRITICAL assets requiring immediate attention",
    table_properties={
        "quality": "silver",
        "delta.enableChangeDataFeed": "true"
    }
)
def critical_alerts():
    """
    Critical assets that need immediate attention.
    This table feeds the Agent Bricks system.
    """
    silver = dlt.read_stream("silver_asset_telemetry")

    return (
        silver
        .filter(F.col("overall_status") == "CRITICAL")
        .select(
            "asset_id",
            "asset_name",
            "site",
            "asset_type",
            "model",
            "vibration_hz",
            "temp_celsius",
            "rpm",
            "voltage_output",
            "vibration_anomaly",
            "temperature_anomaly",
            "overall_status",
            "hours_since_last_maintenance",
            "assigned_technician",
            "manual_version",
            "timestamp",
            "processed_timestamp"
        )
        .withColumn("alert_severity", F.lit("CRITICAL"))
        .withColumn("alert_timestamp", F.current_timestamp())
        .withColumn(
            "predicted_failure_type",
            F.when(F.col("vibration_hz") > 80, F.lit("BEARING_FAILURE"))
             .when(F.col("temp_celsius") > 450, F.lit("COOLING_FAULT"))
             .otherwise(F.lit("GENERAL_ANOMALY"))
        )
    )


# ============================================================================
# GOLD LAYER - Business Aggregates
# ============================================================================

@dlt.table(
    name="gold_asset_health_summary",
    comment="Gold layer: Daily asset health summary for dashboards",
    table_properties={
        "quality": "gold"
    }
)
def gold_asset_health_summary():
    """
    Daily summary of asset health metrics
    """
    silver = dlt.read("silver_asset_telemetry")

    return (
        silver
        .groupBy(
            F.date_trunc("day", "timestamp").alias("date"),
            "site",
            "asset_type",
            "overall_status"
        )
        .agg(
            F.count("*").alias("reading_count"),
            F.avg("vibration_hz").alias("avg_vibration"),
            F.max("vibration_hz").alias("max_vibration"),
            F.avg("temp_celsius").alias("avg_temperature"),
            F.max("temp_celsius").alias("max_temperature"),
            F.countDistinct("asset_id").alias("unique_assets")
        )
    )


@dlt.table(
    name="gold_critical_assets_daily",
    comment="Gold layer: Daily count of critical assets by site",
    table_properties={
        "quality": "gold"
    }
)
def gold_critical_assets_daily():
    """
    Track critical asset counts over time
    """
    alerts = dlt.read("critical_alerts")

    return (
        alerts
        .groupBy(
            F.date_trunc("day", "alert_timestamp").alias("date"),
            "site",
            "asset_type",
            "predicted_failure_type"
        )
        .agg(
            F.countDistinct("asset_id").alias("critical_asset_count"),
            F.avg("vibration_hz").alias("avg_vibration"),
            F.avg("hours_since_last_maintenance").alias("avg_hours_since_maintenance")
        )
    )
