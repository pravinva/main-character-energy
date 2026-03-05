#!/usr/bin/env python3
"""
Generate mock data for Main Character Energy
- sensor_telemetry.csv: 100 assets with sensor readings
- asset_registry.json: master asset list
- maintenance_history.parquet: 3 years of maintenance history
"""

import pandas as pd
import json
from datetime import datetime, timedelta
from faker import Faker
import random
import os

fake = Faker('en_AU')  # Australian locale
random.seed(42)  # For reproducibility

# Output directory
OUTPUT_DIR = "/Users/pravin.varma/Documents/Demo/main-character-energy/workstream-1-foundation/mock_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Asset types and their characteristics
ASSET_TYPES = {
    'wind_turbine': {
        'models': ['Vestas V150-4.2MW', 'Siemens SWT-3.6-120', 'GE 2.5-120'],
        'normal_vibration': (15, 45),
        'normal_temp': (25, 55),
        'normal_rpm': (8, 15),
        'normal_voltage': (650, 690),
        'count': 35
    },
    'gas_turbine': {
        'models': ['GE 7HA.02', 'Siemens SGT-800', 'Mitsubishi M701F'],
        'normal_vibration': (20, 50),
        'normal_temp': (350, 450),
        'normal_rpm': (3000, 3600),
        'normal_voltage': (11000, 13800),
        'count': 20
    },
    'substation': {
        'models': ['ABB 132kV GIS', 'Siemens 8DJ20', 'Schneider SM6'],
        'normal_vibration': (5, 20),
        'normal_temp': (20, 40),
        'normal_rpm': (0, 0),  # No rotation
        'normal_voltage': (132000, 132000),
        'count': 15
    },
    'solar_inverter': {
        'models': ['SMA Sunny Central 2750', 'ABB PVS800', 'Huawei SUN2000-100KTL'],
        'normal_vibration': (2, 10),
        'normal_temp': (30, 60),
        'normal_rpm': (0, 0),
        'normal_voltage': (600, 800),
        'count': 20
    },
    'hydro_unit': {
        'models': ['Andritz Francis 50MW', 'Voith Kaplan 30MW', 'GE Pelton 25MW'],
        'normal_vibration': (25, 55),
        'normal_temp': (35, 65),
        'normal_rpm': (200, 500),
        'normal_voltage': (11000, 22000),
        'count': 10
    }
}

# Australian sites (NSW/VIC)
SITES = [
    'Sydney North Wind Farm, NSW',
    'Melbourne West Solar Park, VIC',
    'Hunter Valley Gas Plant, NSW',
    'Gippsland Hydro Station, VIC',
    'Broken Hill Solar Farm, NSW',
    'Geelong Substation, VIC',
    'Newcastle Wind Farm, NSW',
    'Yarra Valley Hydro, VIC'
]

# Technicians
TECHNICIANS = [
    'James Chen', 'Sarah Williams', 'Michael ODonnell', 'Emma Thompson',
    'David Martinez', 'Lisa Anderson', 'Tom Roberts', 'Rachel Kim'
]

def generate_asset_registry():
    """Generate master asset registry"""
    assets = []
    asset_id = 1

    for asset_type, config in ASSET_TYPES.items():
        for _ in range(config['count']):
            asset = {
                'asset_id': f'MCE-{asset_id:04d}',
                'asset_name': f'{asset_type.replace("_", " ").title()} {asset_id}',
                'asset_type': asset_type,
                'site': random.choice(SITES),
                'model': random.choice(config['models']),
                'serial_number': f'SN{fake.bothify(text="??-######")}',
                'install_date': fake.date_between(start_date='-10y', end_date='-1y').isoformat(),
                'warranty_expiry': fake.date_between(start_date='+1y', end_date='+5y').isoformat(),
                'manual_version': f'v{random.randint(1, 5)}.{random.randint(0, 9)}',
                'assigned_technician': random.choice(TECHNICIANS)
            }
            assets.append(asset)
            asset_id += 1

    # Save as JSON
    output_path = os.path.join(OUTPUT_DIR, 'asset_registry.json')
    with open(output_path, 'w') as f:
        json.dump(assets, f, indent=2)

    print(f"✓ Generated asset_registry.json: {len(assets)} assets")
    return assets

def generate_sensor_telemetry(assets):
    """Generate sensor telemetry CSV with 8 CRITICAL and 5 WARNING assets"""
    telemetry_data = []
    timestamp = datetime.now()

    # Select assets for anomalies
    all_asset_ids = [a['asset_id'] for a in assets]
    critical_assets = random.sample(all_asset_ids, 8)
    warning_assets = random.sample([a for a in all_asset_ids if a not in critical_assets], 5)

    for asset in assets:
        asset_id = asset['asset_id']
        asset_type = asset['asset_type']
        config = ASSET_TYPES[asset_type]

        # Determine if this asset has anomalies
        if asset_id in critical_assets:
            # CRITICAL: vibration > 80Hz
            vibration = random.uniform(80, 120)
            temp = random.uniform(config['normal_temp'][0], config['normal_temp'][1] * 1.3)
        elif asset_id in warning_assets:
            # WARNING: vibration 60-80Hz
            vibration = random.uniform(60, 80)
            temp = random.uniform(config['normal_temp'][0], config['normal_temp'][1] * 1.1)
        else:
            # NORMAL
            vibration = random.uniform(*config['normal_vibration'])
            temp = random.uniform(*config['normal_temp'])

        # Other readings (normal range)
        rpm = random.uniform(*config['normal_rpm']) if config['normal_rpm'][1] > 0 else 0
        voltage = random.uniform(*config['normal_voltage'])

        telemetry_data.append({
            'asset_id': asset_id,
            'asset_name': asset['asset_name'],
            'site': asset['site'],
            'asset_type': asset_type,
            'timestamp': timestamp.isoformat(),
            'vibration_hz': round(vibration, 2),
            'temp_celsius': round(temp, 2),
            'rpm': round(rpm, 2),
            'voltage_output': round(voltage, 2)
        })

    # Save as CSV
    df = pd.DataFrame(telemetry_data)
    output_path = os.path.join(OUTPUT_DIR, 'sensor_telemetry.csv')
    df.to_csv(output_path, index=False)

    critical_count = len([t for t in telemetry_data if t['vibration_hz'] > 80])
    warning_count = len([t for t in telemetry_data if 60 <= t['vibration_hz'] <= 80])

    print(f"✓ Generated sensor_telemetry.csv: {len(telemetry_data)} readings")
    print(f"  - {critical_count} CRITICAL assets (vibration > 80Hz)")
    print(f"  - {warning_count} WARNING assets (vibration 60-80Hz)")

def generate_maintenance_history(assets):
    """Generate 3 years of maintenance history"""
    maintenance_events = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3*365)

    event_types = ['Preventive Maintenance', 'Corrective Repair', 'Emergency Fix',
                   'Inspection', 'Part Replacement', 'Calibration', 'Cleaning']

    for asset in assets:
        # Each asset gets 10-30 maintenance events over 3 years
        num_events = random.randint(10, 30)

        for _ in range(num_events):
            event_date = fake.date_time_between(start_date=start_date, end_date=end_date)
            duration_hours = random.uniform(1, 12)
            downtime_hours = random.uniform(0, duration_hours)

            event = {
                'event_id': fake.uuid4(),
                'asset_id': asset['asset_id'],
                'asset_type': asset['asset_type'],
                'site': asset['site'],
                'event_type': random.choice(event_types),
                'event_date': event_date,
                'technician': random.choice(TECHNICIANS),
                'duration_hours': round(duration_hours, 2),
                'downtime_hours': round(downtime_hours, 2),
                'parts_replaced': random.choice([True, False]),
                'cost_aud': round(random.uniform(500, 15000), 2),
                'notes': fake.sentence(nb_words=10)
            }
            maintenance_events.append(event)

    # Save as Parquet
    df = pd.DataFrame(maintenance_events)
    output_path = os.path.join(OUTPUT_DIR, 'maintenance_history.parquet')
    df.to_parquet(output_path, index=False)

    print(f"✓ Generated maintenance_history.parquet: {len(maintenance_events)} events")

def main():
    print("Generating mock data for Main Character Energy...")
    print("=" * 60)

    # Generate all datasets
    assets = generate_asset_registry()
    generate_sensor_telemetry(assets)
    generate_maintenance_history(assets)

    print("\n" + "=" * 60)
    print("✅ Mock data generation complete!")
    print(f"\nFiles created in: {OUTPUT_DIR}")
    print("  - asset_registry.json")
    print("  - sensor_telemetry.csv")
    print("  - maintenance_history.parquet")

if __name__ == "__main__":
    main()
