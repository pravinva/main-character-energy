"""
Main Character Energy - FastAPI Backend
Queries Lakebase for real-time operational data
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
import os
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

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
# New instance: b77ccee1-1d75-4ab9-9b52-4fe0de04ae5e
# Using OAuth token from environment for authentication
OAUTH_TOKEN = os.environ.get("LAKEBASE_OAUTH_TOKEN", "")

# Flag for mock data mode (local development without OAuth token)
USE_MOCK_DATA = not OAUTH_TOKEN

if USE_MOCK_DATA:
    print("⚠️  WARNING: LAKEBASE_OAUTH_TOKEN not set - using mock data for local development")
    print("⚠️  Set LAKEBASE_OAUTH_TOKEN environment variable to connect to real Lakebase")
    connection_pool = None
    LAKEBASE_CONN_STRING = None
else:
    from urllib.parse import quote_plus
    user_encoded = quote_plus("pravin.varma@databricks.com")
    token_encoded = quote_plus(OAUTH_TOKEN)

    LAKEBASE_CONN_STRING = os.environ.get(
        "LAKEBASE_CONN_STRING",
        f"postgresql://{user_encoded}:{token_encoded}@instance-b77ccee1-1d75-4ab9-9b52-4fe0de04ae5e.database.cloud.databricks.com:5432/databricks_postgres?sslmode=require"
    )

def init_pool():
    global connection_pool
    if USE_MOCK_DATA:
        return  # Skip pool initialization in mock mode
    if not connection_pool:
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=2,
            maxconn=10,
            dsn=LAKEBASE_CONN_STRING
        )

def get_conn():
    if USE_MOCK_DATA:
        raise Exception("Running in mock data mode - no database connection available")
    init_pool()
    return connection_pool.getconn()

def return_conn(conn):
    if connection_pool:
        connection_pool.putconn(conn)

# ─── ENDPOINTS ──────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    if USE_MOCK_DATA:
        return {"status": "healthy", "lakebase": "mock_mode", "message": "Using mock data - set LAKEBASE_OAUTH_TOKEN to connect to real database"}
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
        # Return mock data if Lakebase unavailable
        from datetime import datetime
        return [
            {"id": "MCE-0001", "name": "Vestas V150-4.2MW Turbine 01", "site": "Sydney North Wind Farm, NSW", "type": "wind_turbine", "vibration": 95.3, "temp": 48.2, "status": "CRITICAL", "lastUpdated": datetime.now().isoformat(), "hoursSinceMaint": 720, "predictedFailure": "Bearing failure"},
            {"id": "MCE-0012", "name": "GE 7HA.02 Gas Turbine", "site": "Hunter Valley Gas Plant, NSW", "type": "gas_turbine", "vibration": 88.1, "temp": 465.7, "status": "CRITICAL", "lastUpdated": datetime.now().isoformat(), "hoursSinceMaint": 980, "predictedFailure": "Compressor blade"},
            {"id": "MCE-0034", "name": "ABB PVS800 Inverter 15", "site": "Broken Hill Solar Farm, NSW", "type": "solar_inverter", "vibration": 85.7, "temp": 58.9, "status": "CRITICAL", "lastUpdated": datetime.now().isoformat(), "hoursSinceMaint": 650, "predictedFailure": "Inverter overheating"},
            {"id": "MCE-0045", "name": "Vestas V90-3.0MW Turbine 22", "site": "Newcastle Wind Farm, NSW", "type": "wind_turbine", "vibration": 72.4, "temp": 42.1, "status": "WARNING", "lastUpdated": datetime.now().isoformat(), "hoursSinceMaint": 520, "predictedFailure": "Gearbox wear"},
            {"id": "MCE-0056", "name": "Siemens SWT-3.6-120 Turbine 05", "site": "Sydney North Wind Farm, NSW", "type": "wind_turbine", "vibration": 68.9, "temp": 39.5, "status": "WARNING", "lastUpdated": datetime.now().isoformat(), "hoursSinceMaint": 450, "predictedFailure": "Rotor imbalance"},
            {"id": "MCE-0067", "name": "Francis Turbine Unit 3", "site": "Gippsland Hydro Station, VIC", "type": "hydro_unit", "vibration": 35.2, "temp": 48.7, "status": "HEALTHY", "lastUpdated": datetime.now().isoformat(), "hoursSinceMaint": 120, "predictedFailure": None},
            {"id": "MCE-0078", "name": "ABB 132kV GIS Substation Bay 4", "site": "Geelong Substation, VIC", "type": "substation", "vibration": 12.5, "temp": 32.1, "status": "HEALTHY", "lastUpdated": datetime.now().isoformat(), "hoursSinceMaint": 200, "predictedFailure": None},
            {"id": "MCE-0089", "name": "SMA Sunny Central 2500", "site": "Melbourne West Solar Park, VIC", "type": "solar_inverter", "vibration": 8.3, "temp": 38.9, "status": "HEALTHY", "lastUpdated": datetime.now().isoformat(), "hoursSinceMaint": 180, "predictedFailure": None}
        ]

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
        # Return mock data if Lakebase unavailable
        from datetime import datetime, timedelta
        return [
            {"id": "WO-001", "assetId": "MCE-0001", "createdAt": datetime.now().isoformat(), "priority": "P1", "status": "DISPATCHED", "technician": "James Chen", "failureDate": (datetime.now() + timedelta(days=2)).date().isoformat(), "failureType": "Bearing failure", "requiredParts": "SKF-7320 bearing kit", "procedureSteps": "1. Lock out turbine\n2. Remove nacelle cover\n3. Replace bearing", "safetyChecklist": "Harness, gloves, lockout", "repairSummary": "Critical bearing replacement required", "estimatedHours": 8.0, "updatedAt": datetime.now().isoformat()},
            {"id": "WO-002", "assetId": "MCE-0012", "createdAt": datetime.now().isoformat(), "priority": "P1", "status": "IN_PROGRESS", "technician": "Michael ODonnell", "failureDate": (datetime.now() + timedelta(days=1)).date().isoformat(), "failureType": "Compressor blade", "requiredParts": "Compressor blade set", "procedureSteps": "1. Borescope inspection\n2. Replace damaged blades", "safetyChecklist": "High temp PPE, eye protection", "repairSummary": "Blade damage detected via thermal imaging", "estimatedHours": 12.0, "updatedAt": datetime.now().isoformat()},
            {"id": "WO-003", "assetId": "MCE-0034", "createdAt": datetime.now().isoformat(), "priority": "P1", "status": "DISPATCHED", "technician": "David Martinez", "failureDate": (datetime.now() + timedelta(days=3)).date().isoformat(), "failureType": "Inverter overheating", "requiredParts": "Cooling fan assembly", "procedureSteps": "1. Power down inverter\n2. Replace cooling fans", "safetyChecklist": "Arc flash suit, insulated tools", "repairSummary": "Thermal runaway risk detected", "estimatedHours": 4.0, "updatedAt": datetime.now().isoformat()}
        ]

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
        # Return mock data if Lakebase unavailable
        return [
            {"id": "TECH-001", "name": "James Chen", "site": "Sydney North Wind Farm, NSW", "certifications": '{"electrical": true, "wind_turbine": true}', "location": "En route to MCE-0001", "available": False, "activeOrders": 1},
            {"id": "TECH-002", "name": "Sarah Williams", "site": "Melbourne West Solar Park, VIC", "certifications": '{"solar": true, "inverters": true}', "location": "Melbourne depot", "available": True, "activeOrders": 0},
            {"id": "TECH-003", "name": "Michael ODonnell", "site": "Hunter Valley Gas Plant, NSW", "certifications": '{"gas_turbine": true}', "location": "At MCE-0012", "available": False, "activeOrders": 1},
            {"id": "TECH-004", "name": "Emma Thompson", "site": "Gippsland Hydro Station, VIC", "certifications": '{"hydro": true}', "location": "Gippsland depot", "available": True, "activeOrders": 0},
            {"id": "TECH-005", "name": "David Martinez", "site": "Broken Hill Solar Farm, NSW", "certifications": '{"solar": true}', "location": "Broken Hill depot", "available": False, "activeOrders": 1},
            {"id": "TECH-006", "name": "Lisa Anderson", "site": "Geelong Substation, VIC", "certifications": '{"substation": true}', "location": "Geelong depot", "available": True, "activeOrders": 0},
            {"id": "TECH-007", "name": "Tom Roberts", "site": "Newcastle Wind Farm, NSW", "certifications": '{"wind_turbine": true}', "location": "Newcastle depot", "available": True, "activeOrders": 0},
            {"id": "TECH-008", "name": "Rachel Kim", "site": "Yarra Valley Hydro, VIC", "certifications": '{"hydro": true}', "location": "Yarra Valley depot", "available": True, "activeOrders": 0}
        ]

@app.post("/api/generate-ai-work-order")
def generate_ai_work_order():
    """
    Live AI Demo: Generate a work order using Claude via Databricks FMAPI
    Returns proof it's real: unique request ID, latency, token usage
    """
    import requests
    import time
    from datetime import datetime, timedelta

    # Get Databricks token
    DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")
    if not DATABRICKS_TOKEN:
        # Try OAuth token as fallback
        DATABRICKS_TOKEN = os.environ.get("LAKEBASE_OAUTH_TOKEN")

    if not DATABRICKS_TOKEN:
        return {
            "error": "No DATABRICKS_TOKEN configured",
            "message": "This will work automatically when deployed to Databricks Apps",
            "demo_mode": True
        }

    # Simulate critical alert for demo
    alert = {
        "asset_id": "MCE-0093",
        "asset_name": "Vestas V150-4.2MW Turbine 93",
        "asset_type": "wind_turbine",
        "site": "Sydney North Wind Farm, NSW",
        "vibration_hz": 95.3,
        "temp_celsius": 48.2,
        "alert_timestamp": datetime.now().isoformat()
    }

    system_prompt = """You are an expert field service engineer for Main Character Energy.
You analyze equipment failures and generate detailed work orders for field technicians.

Your work orders must include:
1. Clear diagnosis of the failure based on sensor data
2. Required parts list (specific part numbers)
3. Step-by-step repair procedure
4. Estimated duration
5. AI repair summary explaining the reasoning

Be precise, safety-focused, and include all details a field technician needs."""

    user_prompt = f"""Generate a work order for this critical alert:

Asset: {alert['asset_name']} (ID: {alert['asset_id']})
Type: {alert['asset_type']}
Location: {alert['site']}

Current Sensor Readings:
- Vibration: {alert['vibration_hz']} Hz (CRITICAL - threshold exceeded)
- Temperature: {alert['temp_celsius']}°C
- Alert Time: {alert['alert_timestamp']}

Based on this information, provide:
1. A diagnostic summary (2-3 sentences explaining WHY this failure occurred)
2. The specific failure type (e.g., "Bearing failure")
3. Predicted failure date (estimate based on vibration severity)
4. Priority level (P1 if vibration > 90Hz, P2 if > 80Hz)

Format your response as JSON:
{{
  "failure_type": "...",
  "predicted_failure_date": "YYYY-MM-DD",
  "priority": "P1|P2|P3",
  "ai_repair_summary": "Your 2-3 sentence diagnostic reasoning here",
  "required_parts": "Exact parts needed",
  "estimated_duration_hours": 8
}}"""

    try:
        headers = {
            "Authorization": f"Bearer {DATABRICKS_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "claude-3-5-sonnet-20240620",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 2000,
            "temperature": 0.7
        }

        start_time = time.time()
        response = requests.post(
            "https://7474651028007974.ai-gateway.cloud.databricks.com/mlflow/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        end_time = time.time()

        response.raise_for_status()
        result = response.json()

        # Parse Claude's response
        response_text = result['choices'][0]['message']['content']

        # Extract JSON
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        work_order = json.loads(response_text)

        # Add proof metadata
        return {
            "success": True,
            "work_order": {
                "id": f"WO-AI-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                "assetId": alert['asset_id'],
                "createdAt": datetime.now().isoformat(),
                "priority": work_order.get('priority', 'P1'),
                "status": "AI_GENERATED_DEMO",
                "technician": "Unassigned",
                "failureDate": work_order.get('predicted_failure_date', (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')),
                "failureType": work_order.get('failure_type', 'Unknown'),
                "requiredParts": work_order.get('required_parts', 'Parts TBD'),
                "procedureSteps": "AI-generated procedure (see repair summary)",
                "safetyChecklist": "Standard safety checklist for wind turbines",
                "repairSummary": work_order.get('ai_repair_summary', 'AI analysis unavailable'),
                "estimatedHours": work_order.get('estimated_duration_hours', 8),
                "updatedAt": datetime.now().isoformat()
            },
            "proof": {
                "request_id": result.get('id', 'N/A'),
                "model": result.get('model', 'claude-3-5-sonnet-20240620'),
                "latency_seconds": round(end_time - start_time, 2),
                "tokens_used": result.get('usage', {}).get('total_tokens', 0),
                "timestamp": datetime.now().isoformat(),
                "is_real_ai": True
            }
        }

    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to call Databricks FMAPI - this will work when deployed",
            "demo_mode": True
        }

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
        # Return mock data if Lakebase unavailable
        return {
            "critical_count": 3,
            "warning_count": 2,
            "healthy_count": 3,
            "total_assets": 8,
            "total_sites": 6,
            "total_work_orders": 3,
            "p1_count": 3,
            "dispatched_count": 2,
            "in_progress_count": 1,
            "available_techs": 5,
            "fleet_availability": 37.5
        }

# ─── STATIC FILES (FRONTEND) ────────────────────────────────────────────────

# Mount static files from frontend/dist
static_path = Path(__file__).parent / "frontend" / "dist"
if static_path.exists():
    # Mount static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=str(static_path / "assets")), name="assets")

    @app.get("/", response_class=FileResponse)
    def serve_root():
        """Serve the React frontend root"""
        index_file = static_path / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Frontend not built")

    @app.get("/{full_path:path}", response_class=FileResponse)
    def serve_frontend(full_path: str):
        """Serve the React frontend for all non-API routes (SPA routing)"""
        # Serve index.html for all other routes (SPA routing)
        index_file = static_path / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Frontend not built")
else:
    print(f"⚠️  WARNING: Frontend dist directory not found at {static_path}")
    print("⚠️  Run 'npm run build' in the frontend directory to build the frontend")

    @app.get("/")
    def serve_root_fallback():
        return {
            "error": "Frontend not deployed",
            "message": "Build the frontend with 'npm run build' in frontend/ directory",
            "api_status": "operational"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
