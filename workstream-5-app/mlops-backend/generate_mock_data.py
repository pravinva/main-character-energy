"""
Mock Data Generation for Main Character Energy
Generates realistic IoT telemetry and maintenance history datasets
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import random

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

def generate_asset_registry(n_assets=100):
    """Generate asset registry with diverse equipment types"""

    asset_types = [
        {"type": "wind_turbine", "models": ["Vestas V150-4.2MW", "Siemens SWT-3.6-120", "GE 2.5-120"], "count": 40},
        {"type": "solar_inverter", "models": ["ABB PVS800", "SMA Sunny Central", "Fronius Symo"], "count": 30},
        {"type": "gas_turbine", "models": ["GE 7HA.02", "Siemens SGT-800", "MHI M501J"], "count": 15},
        {"type": "hydro_unit", "models": ["Francis Turbine", "Kaplan Turbine", "Pelton Wheel"], "count": 10},
        {"type": "substation", "models": ["ABB 132kV GIS", "Siemens 220kV AIS", "GE Prolec"], "count": 5}
    ]

    sites = [
        "Sydney North Wind Farm, NSW",
        "Melbourne West Solar Park, VIC",
        "Hunter Valley Gas Plant, NSW",
        "Gippsland Hydro Station, VIC",
        "Broken Hill Solar Farm, NSW",
        "Newcastle Wind Farm, NSW",
        "Geelong Substation, VIC",
        "Yarra Valley Hydro, VIC",
        "Port Augusta Solar, SA",
        "Whyalla Wind Farm, SA"
    ]

    assets = []
    asset_id = 1

    for asset_type_info in asset_types:
        for _ in range(asset_type_info["count"]):
            model = random.choice(asset_type_info["models"])
            site = random.choice(sites)

            assets.append({
                "asset_id": f"MCE-{asset_id:04d}",
                "asset_name": f"{model} Unit {asset_id:02d}",
                "asset_type": asset_type_info["type"],
                "site": site,
                "commissioned_date": (datetime.now() - timedelta(days=random.randint(365, 3650))).strftime("%Y-%m-%d"),
                "rated_capacity_mw": round(random.uniform(1.0, 10.0), 2) if asset_type_info["type"] != "substation" else None,
                "manufacturer": model.split()[0],
                "serial_number": f"SN-{random.randint(100000, 999999)}"
            })
            asset_id += 1

    return pd.DataFrame(assets)

def generate_sensor_telemetry(asset_registry, hours=168, critical_count=5):
    """
    Generate IoT sensor telemetry for the past week (168 hours)
    Ensures exactly 'critical_count' assets have vibration > 80Hz
    """

    # Baseline parameters by asset type
    vibration_baselines = {
        "wind_turbine": {"mean": 45, "std": 15, "critical_threshold": 80},
        "solar_inverter": {"mean": 15, "std": 8, "critical_threshold": 80},
        "gas_turbine": {"mean": 65, "std": 20, "critical_threshold": 80},
        "hydro_unit": {"mean": 30, "std": 10, "critical_threshold": 80},
        "substation": {"mean": 10, "std": 5, "critical_threshold": 80}
    }

    temp_baselines = {
        "wind_turbine": {"mean": 42, "std": 8},
        "solar_inverter": {"mean": 55, "std": 12},
        "gas_turbine": {"mean": 450, "std": 50},
        "hydro_unit": {"mean": 48, "std": 5},
        "substation": {"mean": 32, "std": 6}
    }

    # Select random assets to be critical
    critical_assets = random.sample(list(asset_registry["asset_id"]), critical_count)
    print(f"Critical assets (vibration > 80Hz): {critical_assets}")

    telemetry_data = []
    base_time = datetime.now() - timedelta(hours=hours)

    for _, asset in asset_registry.iterrows():
        asset_id = asset["asset_id"]
        asset_type = asset["asset_type"]

        # Get baseline parameters
        vib_params = vibration_baselines[asset_type]
        temp_params = temp_baselines[asset_type]

        # Determine if this asset should be critical
        is_critical = asset_id in critical_assets

        for hour in range(hours):
            timestamp = base_time + timedelta(hours=hour)

            # Generate vibration data
            if is_critical:
                # Critical assets: vibration increases over time, peaks > 80Hz
                trend = (hour / hours) * 30  # Gradual increase
                vibration = vib_params["mean"] + trend + np.random.normal(0, 5)
                vibration = max(85, min(vibration, 120))  # Ensure > 80Hz but realistic
            else:
                # Normal assets: random walk around baseline
                vibration = max(0, np.random.normal(vib_params["mean"], vib_params["std"]))
                vibration = min(vibration, 75)  # Cap below critical threshold

            # Generate temperature data (correlated with vibration for realism)
            temp_offset = (vibration - vib_params["mean"]) * 0.3
            temperature = max(0, np.random.normal(temp_params["mean"] + temp_offset, temp_params["std"]))

            # Additional sensor metrics
            pressure = max(0, np.random.normal(3.5, 0.5))  # bar
            power_output = max(0, np.random.normal(
                asset["rated_capacity_mw"] * 0.75 if asset["rated_capacity_mw"] else 0,
                asset["rated_capacity_mw"] * 0.15 if asset["rated_capacity_mw"] else 0
            )) if asset["rated_capacity_mw"] else None

            telemetry_data.append({
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "asset_id": asset_id,
                "vibration_hz": round(vibration, 2),
                "temp_celsius": round(temperature, 2),
                "pressure_bar": round(pressure, 2),
                "power_output_mw": round(power_output, 2) if power_output else None,
                "operating_hours": round(hour + random.uniform(0, 1), 2),
                "status": "CRITICAL" if vibration > 80 else "WARNING" if vibration > 65 else "HEALTHY"
            })

    return pd.DataFrame(telemetry_data)

def generate_maintenance_history(asset_registry):
    """Generate historical maintenance records"""

    maintenance_types = [
        "Scheduled inspection",
        "Bearing replacement",
        "Oil change",
        "Blade adjustment",
        "Inverter firmware update",
        "Cooling system service",
        "Vibration sensor calibration",
        "Emergency repair"
    ]

    history = []

    for _, asset in asset_registry.iterrows():
        # Generate 3-8 maintenance records per asset
        n_records = random.randint(3, 8)

        for i in range(n_records):
            maintenance_date = datetime.now() - timedelta(days=random.randint(30, 1095))

            history.append({
                "asset_id": asset["asset_id"],
                "maintenance_date": maintenance_date.strftime("%Y-%m-%d"),
                "maintenance_type": random.choice(maintenance_types),
                "technician": random.choice(["James Chen", "Sarah Williams", "Michael O'Donnell", "Emma Thompson", "David Martinez"]),
                "work_performed": f"Performed {random.choice(maintenance_types).lower()}",
                "parts_replaced": random.choice(["Bearing kit", "Oil filter", "Sensor module", "None", "Blade components"]),
                "downtime_hours": round(random.uniform(0.5, 8.0), 1),
                "cost_aud": round(random.uniform(500, 25000), 2),
                "notes": "Completed successfully" if random.random() > 0.1 else "Follow-up required"
            })

    return pd.DataFrame(history).sort_values("maintenance_date", ascending=False)

def generate_technical_manuals():
    """Generate mock technical manual content as text files (PDFs in production)"""

    manuals = {
        "Vestas_V150_Maintenance_Manual.txt": """
VESTAS V150-4.2MW WIND TURBINE MAINTENANCE MANUAL

CRITICAL SAFETY PROCEDURES:
- Always engage lockout/tagout before entering nacelle
- Wear fall protection harness at all times
- Maximum wind speed for maintenance: 15 m/s
- Minimum crew size: 2 technicians

VIBRATION TROUBLESHOOTING (>80Hz):
1. Check main bearing condition - look for metal shavings in oil
2. Inspect gearbox for gear tooth wear
3. Verify blade balance using laser alignment tool
4. Check tower bolts for loosening

REQUIRED PARTS FOR BEARING REPLACEMENT:
- SKF 7320 BECBM main bearing kit (Part #: V150-BR-001)
- High-temperature bearing grease (5kg)
- Hydraulic puller set
- Torque wrench (0-2000 Nm)

ESTIMATED REPAIR TIME: 8-12 hours
        """,

        "ABB_PVS800_Inverter_Manual.txt": """
ABB PVS800 SOLAR INVERTER SERVICE MANUAL

SAFETY CHECKLIST:
- De-energize DC input before accessing internals
- Verify zero voltage with multimeter
- Wear arc flash rated PPE (40 cal/cm²)
- Use insulated tools only

OVERHEATING DIAGNOSIS (Temp > 70°C):
1. Inspect cooling fan operation - replace if faulty
2. Clean heat sink fins (compressed air)
3. Check ambient temperature < 45°C
4. Verify airflow clearance (min 1m on all sides)

REQUIRED PARTS FOR COOLING FAN REPLACEMENT:
- ABB cooling fan assembly (Part #: PVS800-FAN-02)
- Fan controller board
- Thermal paste

ESTIMATED REPAIR TIME: 2-4 hours
        """,

        "GE_7HA_Gas_Turbine_Manual.txt": """
GE 7HA.02 GAS TURBINE MAINTENANCE MANUAL

CRITICAL SAFETY:
- Hot gas path temperature exceeds 1400°C
- Mandatory 24-hour cooldown before inspection
- High-temperature PPE required (rating: 600°C)
- Gas detection equipment mandatory

COMPRESSOR BLADE FAILURE (High vibration + temp):
1. Perform borescope inspection of all stages
2. Check for foreign object damage (FOD)
3. Inspect blade dovetails for cracking
4. Verify stage 1 blade tip clearance

REQUIRED PARTS FOR BLADE REPLACEMENT:
- Stage 1-3 compressor blade set (Part #: 7HA-CB-S123)
- Blade root locking pins
- High-temp anti-seize compound

ESTIMATED REPAIR TIME: 12-16 hours
        """
    }

    return manuals

def save_datasets(asset_registry, telemetry, maintenance, manuals, output_dir="./data"):
    """Save all generated datasets"""

    import os
    os.makedirs(output_dir, exist_ok=True)

    # Save CSV files
    asset_registry.to_csv(f"{output_dir}/asset_registry.csv", index=False)
    telemetry.to_csv(f"{output_dir}/sensor_telemetry.csv", index=False)
    maintenance.to_csv(f"{output_dir}/maintenance_history.csv", index=False)

    # Save JSON version of telemetry (for streaming simulation)
    telemetry.to_json(f"{output_dir}/sensor_telemetry.json", orient="records", indent=2)

    # Save technical manuals
    manuals_dir = f"{output_dir}/technical_manuals"
    os.makedirs(manuals_dir, exist_ok=True)
    for filename, content in manuals.items():
        with open(f"{manuals_dir}/{filename}", "w") as f:
            f.write(content)

    print("\n" + "=" * 80)
    print("MOCK DATA GENERATION COMPLETE")
    print("=" * 80)
    print(f"""
Files generated in '{output_dir}/':
  ✓ asset_registry.csv ({len(asset_registry)} assets)
  ✓ sensor_telemetry.csv ({len(telemetry)} records)
  ✓ sensor_telemetry.json (streaming format)
  ✓ maintenance_history.csv ({len(maintenance)} records)
  ✓ technical_manuals/ (3 equipment manuals)

Statistics:
  - Total assets: {len(asset_registry)}
  - Critical assets (vibration > 80Hz): {len(telemetry[telemetry['status'] == 'CRITICAL']['asset_id'].unique())}
  - Time range: {telemetry['timestamp'].min()} to {telemetry['timestamp'].max()}
  - Sampling frequency: 1 hour

Next steps:
  1. Upload CSV files to Unity Catalog Volume: /Volumes/field_operations/bronze/iot_telemetry_raw/
  2. Upload technical manuals to: /Volumes/field_operations/bronze/technical_manuals/
  3. Run Lakeflow pipeline to ingest data
    """)

if __name__ == "__main__":
    print("Generating mock datasets for Main Character Energy...")
    print("=" * 80)

    # Generate datasets
    print("\n[1/4] Generating asset registry (100 assets)...")
    asset_registry = generate_asset_registry(n_assets=100)
    print(f"✓ Generated {len(asset_registry)} assets")

    print("\n[2/4] Generating IoT sensor telemetry (168 hours, 5 critical assets)...")
    telemetry = generate_sensor_telemetry(asset_registry, hours=168, critical_count=5)
    print(f"✓ Generated {len(telemetry)} telemetry records")

    print("\n[3/4] Generating maintenance history...")
    maintenance = generate_maintenance_history(asset_registry)
    print(f"✓ Generated {len(maintenance)} maintenance records")

    print("\n[4/4] Generating technical manuals...")
    manuals = generate_technical_manuals()
    print(f"✓ Generated {len(manuals)} technical manuals")

    # Save all datasets
    save_datasets(asset_registry, telemetry, maintenance, manuals)
