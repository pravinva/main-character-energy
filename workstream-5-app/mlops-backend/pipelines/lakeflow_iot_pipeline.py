"""
Lakeflow Spark Declarative Pipeline for Main Character Energy
Ingests IoT telemetry, detects anomalies, and creates Critical Alerts

This pipeline demonstrates:
1. Bronze layer: Raw data ingestion from Unity Catalog Volumes
2. Silver layer: Data quality, anomaly detection (vibration > 80Hz)
3. Gold layer: Business-ready aggregations and predictions
"""

import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *

# ============================================================================
# BRONZE LAYER: Raw Data Ingestion
# ============================================================================

@dlt.table(
    name="bronze_sensor_telemetry",
    comment="Raw IoT sensor telemetry from equipment (Bronze Layer)",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.zOrderCols": "asset_id,timestamp"
    }
)
def bronze_sensor_telemetry():
    """
    Ingest raw IoT sensor data from Unity Catalog Volume
    Volume path: /Volumes/field_operations/bronze/iot_telemetry_raw/sensor_telemetry.csv
    """
    return (
        spark.read
        .format("csv")
        .option("header", "true")
        .option("inferSchema", "true")
        .load("/Volumes/field_operations/bronze/iot_telemetry_raw/sensor_telemetry.csv")
        .withColumn("ingestion_timestamp", F.current_timestamp())
        .withColumn("source_file", F.input_file_name())
    )

@dlt.table(
    name="bronze_maintenance_history",
    comment="Historical maintenance records (Bronze Layer)"
)
def bronze_maintenance_history():
    """
    Ingest maintenance history data from Unity Catalog Volume
    """
    return (
        spark.read
        .format("csv")
        .option("header", "true")
        .option("inferSchema", "true")
        .load("/Volumes/field_operations/bronze/iot_telemetry_raw/maintenance_history.csv")
        .withColumn("ingestion_timestamp", F.current_timestamp())
    )

@dlt.table(
    name="bronze_asset_registry",
    comment="Asset registry and metadata (Bronze Layer)"
)
def bronze_asset_registry():
    """
    Ingest asset registry from Unity Catalog Volume
    """
    return (
        spark.read
        .format("csv")
        .option("header", "true")
        .option("inferSchema", "true")
        .load("/Volumes/field_operations/bronze/iot_telemetry_raw/asset_registry.csv")
        .withColumn("ingestion_timestamp", F.current_timestamp())
    )

# ============================================================================
# SILVER LAYER: Data Quality & Anomaly Detection
# ============================================================================

@dlt.table(
    name="silver_sensor_telemetry_clean",
    comment="Cleaned and validated sensor telemetry (Silver Layer)",
    table_properties={
        "quality": "silver",
        "delta.enableChangeDataFeed": "true"
    }
)
@dlt.expect_all_or_drop({
    "valid_timestamp": "timestamp IS NOT NULL",
    "valid_asset_id": "asset_id IS NOT NULL",
    "valid_vibration": "vibration_hz >= 0 AND vibration_hz < 200",
    "valid_temperature": "temp_celsius >= -50 AND temp_celsius < 1500"
})
def silver_sensor_telemetry_clean():
    """
    Apply data quality rules and enrich with asset metadata
    - Drop nulls and invalid values
    - Join with asset registry for enrichment
    - Calculate running statistics
    """
    bronze_telemetry = dlt.read("bronze_sensor_telemetry")
    asset_registry = dlt.read("bronze_asset_registry")

    return (
        bronze_telemetry
        .join(asset_registry, on="asset_id", how="left")
        .select(
            F.col("timestamp").cast("timestamp").alias("timestamp"),
            F.col("asset_id"),
            F.col("asset_name"),
            F.col("asset_type"),
            F.col("site"),
            F.col("vibration_hz"),
            F.col("temp_celsius"),
            F.col("pressure_bar"),
            F.col("power_output_mw"),
            F.col("operating_hours"),
            F.col("status"),
            F.col("ingestion_timestamp")
        )
        .withColumn("processing_timestamp", F.current_timestamp())
    )

@dlt.table(
    name="silver_critical_alerts",
    comment="Real-time anomaly detection: Critical asset alerts (vibration > 80Hz)",
    table_properties={
        "quality": "silver",
        "delta.enableChangeDataFeed": "true",
        "pipelines.trigger": "continuous"
    }
)
@dlt.expect_or_fail("critical_vibration", "vibration_hz > 80")
def silver_critical_alerts():
    """
    ANOMALY DETECTION: Flag assets with vibration > 80Hz
    This table triggers AI agent work order generation
    """
    clean_telemetry = dlt.read("silver_sensor_telemetry_clean")

    # Get latest reading per asset
    latest_readings = (
        clean_telemetry
        .withColumn("row_num", F.row_number().over(
            Window.partitionBy("asset_id").orderBy(F.desc("timestamp"))
        ))
        .filter(F.col("row_num") == 1)
    )

    # Flag critical assets
    critical_assets = (
        latest_readings
        .filter(F.col("vibration_hz") > 80)
        .select(
            F.col("asset_id"),
            F.col("asset_name"),
            F.col("asset_type"),
            F.col("site"),
            F.col("timestamp").alias("alert_timestamp"),
            F.col("vibration_hz"),
            F.col("temp_celsius"),
            F.col("pressure_bar"),
            F.lit("CRITICAL_VIBRATION").alias("alert_type"),
            F.lit("Vibration exceeds critical threshold (80Hz)").alias("alert_description"),
            F.current_timestamp().alias("created_at"),
            F.lit(False).alias("work_order_created")  # Flag for agent processing
        )
    )

    return critical_assets

@dlt.table(
    name="silver_predictive_scores",
    comment="Predictive failure scores using simple heuristics"
)
def silver_predictive_scores():
    """
    Calculate predictive failure scores based on:
    - Vibration level
    - Temperature deviation
    - Time since last maintenance
    """
    clean_telemetry = dlt.read("silver_sensor_telemetry_clean")
    maintenance_history = dlt.read("bronze_maintenance_history")

    # Get days since last maintenance
    latest_maintenance = (
        maintenance_history
        .groupBy("asset_id")
        .agg(F.max("maintenance_date").alias("last_maintenance_date"))
    )

    # Get latest telemetry per asset
    latest_telemetry = (
        clean_telemetry
        .withColumn("row_num", F.row_number().over(
            Window.partitionBy("asset_id").orderBy(F.desc("timestamp"))
        ))
        .filter(F.col("row_num") == 1)
    )

    # Calculate failure probability score
    scored_assets = (
        latest_telemetry
        .join(latest_maintenance, on="asset_id", how="left")
        .withColumn("days_since_maintenance",
            F.datediff(F.current_date(), F.col("last_maintenance_date")))
        .withColumn("vibration_score",
            F.when(F.col("vibration_hz") > 80, 1.0)
             .when(F.col("vibration_hz") > 65, 0.6)
             .when(F.col("vibration_hz") > 50, 0.3)
             .otherwise(0.1))
        .withColumn("maintenance_score",
            F.when(F.col("days_since_maintenance") > 180, 0.8)
             .when(F.col("days_since_maintenance") > 90, 0.4)
             .otherwise(0.1))
        .withColumn("failure_probability",
            F.round((F.col("vibration_score") * 0.7 + F.col("maintenance_score") * 0.3), 3))
        .withColumn("predicted_failure_date",
            F.when(F.col("failure_probability") > 0.7,
                F.date_add(F.current_date(), 7))  # 7 days
             .when(F.col("failure_probability") > 0.4,
                F.date_add(F.current_date(), 14))  # 14 days
             .otherwise(F.date_add(F.current_date(), 30)))  # 30 days
        .select(
            "asset_id", "asset_name", "site", "asset_type",
            "vibration_hz", "temp_celsius",
            "days_since_maintenance",
            "failure_probability",
            "predicted_failure_date",
            F.current_timestamp().alias("scored_at")
        )
    )

    return scored_assets

# ============================================================================
# GOLD LAYER: Business-Ready Aggregations
# ============================================================================

@dlt.table(
    name="gold_asset_health_summary",
    comment="Aggregated asset health metrics (Gold Layer)",
    table_properties={
        "quality": "gold"
    }
)
def gold_asset_health_summary():
    """
    Create executive dashboard metrics
    - Current status by site
    - Average health scores
    - Critical asset counts
    """
    clean_telemetry = dlt.read("silver_sensor_telemetry_clean")
    predictive_scores = dlt.read("silver_predictive_scores")

    # Get latest status per asset
    latest_status = (
        clean_telemetry
        .withColumn("row_num", F.row_number().over(
            Window.partitionBy("asset_id").orderBy(F.desc("timestamp"))
        ))
        .filter(F.col("row_num") == 1)
    )

    # Aggregate by site
    site_summary = (
        latest_status
        .join(predictive_scores, on="asset_id", how="left")
        .groupBy("site")
        .agg(
            F.count("asset_id").alias("total_assets"),
            F.sum(F.when(F.col("status") == "CRITICAL", 1).otherwise(0)).alias("critical_count"),
            F.sum(F.when(F.col("status") == "WARNING", 1).otherwise(0)).alias("warning_count"),
            F.sum(F.when(F.col("status") == "HEALTHY", 1).otherwise(0)).alias("healthy_count"),
            F.round(F.avg("vibration_hz"), 2).alias("avg_vibration_hz"),
            F.round(F.avg("temp_celsius"), 2).alias("avg_temp_celsius"),
            F.round(F.avg("failure_probability"), 3).alias("avg_failure_probability"),
            F.current_timestamp().alias("updated_at")
        )
    )

    return site_summary

@dlt.table(
    name="gold_first_time_fix_metrics",
    comment="First-Time Fix Rate calculation (Gold Layer)"
)
def gold_first_time_fix_metrics():
    """
    Calculate First-Time Fix Rate from maintenance history
    Metric: % of repairs completed without return visit
    """
    maintenance_history = dlt.read("bronze_maintenance_history")

    # Calculate if follow-up was required
    ftf_metrics = (
        maintenance_history
        .withColumn("is_first_time_fix",
            F.when(F.col("notes") == "Completed successfully", 1).otherwise(0))
        .groupBy("asset_id")
        .agg(
            F.count("*").alias("total_maintenance_events"),
            F.sum("is_first_time_fix").alias("first_time_fixes")
        )
        .withColumn("first_time_fix_rate",
            F.round((F.col("first_time_fixes") / F.col("total_maintenance_events")) * 100, 2))
        .withColumn("calculated_at", F.current_timestamp())
    )

    return ftf_metrics

# ============================================================================
# AGENT LAYER: Tables for AI Agent Framework
# ============================================================================

@dlt.table(
    name="agents_unprocessed_alerts",
    comment="Critical alerts awaiting AI agent processing",
    table_properties={
        "delta.enableChangeDataFeed": "true"
    }
)
def agents_unprocessed_alerts():
    """
    View of critical alerts that haven't been processed by AI agents
    This is monitored by the Agent Bricks framework
    """
    critical_alerts = dlt.read("silver_critical_alerts")

    unprocessed = (
        critical_alerts
        .filter(F.col("work_order_created") == False)
        .select(
            "asset_id",
            "asset_name",
            "asset_type",
            "site",
            "alert_timestamp",
            "vibration_hz",
            "temp_celsius",
            "alert_type",
            "alert_description",
            "created_at"
        )
    )

    return unprocessed

print("""
Lakeflow Pipeline Definition Complete

Tables created:
  Bronze Layer:
    - bronze_sensor_telemetry
    - bronze_maintenance_history
    - bronze_asset_registry

  Silver Layer:
    - silver_sensor_telemetry_clean (with DQ checks)
    - silver_critical_alerts (vibration > 80Hz)
    - silver_predictive_scores (failure probability)

  Gold Layer:
    - gold_asset_health_summary
    - gold_first_time_fix_metrics

  Agent Layer:
    - agents_unprocessed_alerts (for AI agent consumption)

Deploy this pipeline with:
  databricks pipelines create \\
    --name "mce-field-operations-pipeline" \\
    --storage "dbfs:/pipelines/mce_field_ops" \\
    --target "field_operations" \\
    --notebook-path "./pipelines/lakeflow_iot_pipeline.py" \\
    --continuous
""")
