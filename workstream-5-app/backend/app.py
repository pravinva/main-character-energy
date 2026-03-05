"""
Main Character Energy - FastAPI Backend
Queries Lakebase for real-time operational data
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
import os
from typing import List, Dict, Any
from datetime import datetime

app = FastAPI(title="Main Character Energy API", version="1.0.0")

# CORS for Databricks App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lakebase connection pool
LAKEBASE_CONN_STRING = os.environ.get(
    "LAKEBASE_CONN_STRING",
    "postgresql://mce_service:MCE_Service_2026!@ep-tiny-field-d2xsbyci.database.us-east-1.cloud.databricks.com:5432/databricks_postgres?sslmode=require"
)

connection_pool = None

def init_pool():
    global connection_pool
    if not connection_pool:
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=2,
            maxconn=10,
            dsn=LAKEBASE_CONN_STRING
        )

def get_conn():
    init_pool()
    return connection_pool.getconn()

def return_conn(conn):
    connection_pool.putconn(conn)

# ─── ENDPOINTS ──────────────────────────────────────────────────────────────

@app.get("/")
def read_root():
    return {
        "service": "Main Character Energy API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
def health_check():
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        return_conn(conn)
        return {"status": "healthy", "lakebase": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Lakebase connection failed: {str(e)}")

@app.get("/api/assets", response_model=List[Dict[str, Any]])
def get_assets():
    """Get all assets with current status"""
    conn = None
    try:
        conn = get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT
                asset_id as id,
                asset_name as name,
                site,
                asset_type as type,
                vibration_hz as vibration,
                temp_celsius as temp,
                status,
                last_updated as "lastUpdated",
                hours_since_last_maintenance as "hoursSinceMaint",
                predicted_failure_type as "predictedFailure"
            FROM mce_operations.mce_assets_live_status
            ORDER BY
                CASE status
                    WHEN 'CRITICAL' THEN 1
                    WHEN 'WARNING' THEN 2
                    ELSE 3
                END,
                vibration_hz DESC
        """)

        assets = cursor.fetchall()
        cursor.close()
        return_conn(conn)

        return [dict(row) for row in assets]

    except Exception as e:
        if conn:
            return_conn(conn)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/work-orders", response_model=List[Dict[str, Any]])
def get_work_orders():
    """Get all active work orders"""
    conn = None
    try:
        conn = get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT
                work_order_id as id,
                asset_id as "assetId",
                created_at as "createdAt",
                priority,
                status,
                assigned_technician as technician,
                predicted_failure_date as "failureDate",
                predicted_failure_type as "failureType",
                required_parts as "requiredParts",
                procedure_steps as "procedureSteps",
                safety_checklist as "safetyChecklist",
                ai_repair_summary as "repairSummary",
                estimated_duration_hours as "estimatedHours",
                updated_at as "updatedAt"
            FROM mce_operations.mce_work_orders
            WHERE status IN ('DISPATCHED', 'IN_PROGRESS')
            ORDER BY
                CASE priority
                    WHEN 'P1' THEN 1
                    WHEN 'P2' THEN 2
                    WHEN 'P3' THEN 3
                END,
                created_at DESC
        """)

        orders = cursor.fetchall()
        cursor.close()
        return_conn(conn)

        return [dict(row) for row in orders]

    except Exception as e:
        if conn:
            return_conn(conn)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/technicians", response_model=List[Dict[str, Any]])
def get_technicians():
    """Get all field technicians"""
    conn = None
    try:
        conn = get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT
                technician_id as id,
                name,
                site,
                certifications,
                current_location as location,
                available,
                active_work_orders as "activeOrders"
            FROM mce_operations.mce_technicians
            ORDER BY available DESC, name
        """)

        techs = cursor.fetchall()
        cursor.close()
        return_conn(conn)

        return [dict(row) for row in techs]

    except Exception as e:
        if conn:
            return_conn(conn)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard-stats")
def get_dashboard_stats():
    """Get aggregated dashboard statistics"""
    conn = None
    try:
        conn = get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Asset counts by status
        cursor.execute("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'CRITICAL') as critical_count,
                COUNT(*) FILTER (WHERE status = 'WARNING') as warning_count,
                COUNT(*) FILTER (WHERE status = 'HEALTHY') as healthy_count,
                COUNT(*) as total_assets,
                COUNT(DISTINCT site) as total_sites
            FROM mce_operations.mce_assets_live_status
        """)
        asset_stats = dict(cursor.fetchone())

        # Work order counts
        cursor.execute("""
            SELECT
                COUNT(*) as total_work_orders,
                COUNT(*) FILTER (WHERE priority = 'P1') as p1_count,
                COUNT(*) FILTER (WHERE status = 'DISPATCHED') as dispatched_count,
                COUNT(*) FILTER (WHERE status = 'IN_PROGRESS') as in_progress_count
            FROM mce_operations.mce_work_orders
            WHERE status IN ('DISPATCHED', 'IN_PROGRESS')
        """)
        wo_stats = dict(cursor.fetchone())

        # Available technicians
        cursor.execute("""
            SELECT COUNT(*) as available_techs
            FROM mce_operations.mce_technicians
            WHERE available = true
        """)
        tech_stats = dict(cursor.fetchone())

        cursor.close()
        return_conn(conn)

        return {
            **asset_stats,
            **wo_stats,
            **tech_stats,
            "fleet_availability": round(
                (asset_stats['healthy_count'] / asset_stats['total_assets'] * 100)
                if asset_stats['total_assets'] > 0 else 0,
                1
            )
        }

    except Exception as e:
        if conn:
            return_conn(conn)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
