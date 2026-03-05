"""
Test AI Agent - Generate Live Work Order with Claude via Databricks FMAPI
Run this to see Claude AI actually generate a work order in real-time
"""

import os
import requests
import json
from datetime import datetime

# Databricks FMAPI endpoint
FMAPI_ENDPOINT = "https://7474651028007974.ai-gateway.cloud.databricks.com/mlflow/v1/chat/completions"

def get_databricks_token():
    """Get Databricks token from environment or profile"""
    token = os.environ.get("DATABRICKS_TOKEN")
    if not token:
        # Try to get from databricks CLI
        import subprocess
        try:
            result = subprocess.run(
                ["databricks", "auth", "token", "--profile", "fe-vm"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                token = result.stdout.strip()
        except:
            pass
    return token

def generate_work_order_with_ai():
    """Call Claude AI via Databricks FMAPI to generate a work order"""

    print("=" * 80)
    print("LIVE AI WORK ORDER GENERATION TEST")
    print("=" * 80)

    # Get token
    token = get_databricks_token()
    if not token:
        print("❌ DATABRICKS_TOKEN not found")
        print("   Set it with: export DATABRICKS_TOKEN='dapi...'")
        return

    print(f"✓ Using Databricks token (length: {len(token)})")
    print(f"✓ FMAPI Endpoint: {FMAPI_ENDPOINT}")

    # Mock critical alert
    alert = {
        "asset_id": "MCE-0093",
        "asset_name": "Vestas V150-4.2MW Turbine 93",
        "asset_type": "wind_turbine",
        "site": "Sydney North Wind Farm, NSW",
        "vibration_hz": 95.3,
        "temp_celsius": 48.2,
        "alert_timestamp": datetime.now().isoformat()
    }

    print(f"\n📊 Simulated Critical Alert:")
    print(f"   Asset: {alert['asset_name']}")
    print(f"   Vibration: {alert['vibration_hz']} Hz (CRITICAL - threshold: 80Hz)")
    print(f"   Temperature: {alert['temp_celsius']}°C")
    print(f"   Timestamp: {alert['alert_timestamp']}")

    # Technical manual reference
    technical_manual = {
        "required_parts": "SKF 7320 BECBM main bearing kit (Part #: V150-BR-001), High-temperature bearing grease (5kg)",
        "estimated_hours": 8,
        "failure_indicators": "High vibration (>80Hz), metal shavings in oil, unusual noise"
    }

    # Construct prompt for Claude
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

Technical Manual Reference:
Required Parts: {technical_manual['required_parts']}
Estimated Duration: {technical_manual['estimated_hours']} hours
Failure Indicators: {technical_manual['failure_indicators']}

Based on this information, provide:
1. A diagnostic summary (2-3 sentences explaining WHY this failure occurred)
2. The specific failure type (e.g., "Bearing failure", "Inverter overheating")
3. Predicted failure date (estimate based on vibration severity)
4. Priority level (P1 if vibration > 90Hz, P2 if > 80Hz, P3 otherwise)

Format your response as JSON:
{{
  "failure_type": "...",
  "predicted_failure_date": "YYYY-MM-DD",
  "priority": "P1|P2|P3",
  "ai_repair_summary": "Your 2-3 sentence diagnostic reasoning here",
  "required_parts": "Exact parts needed",
  "estimated_duration_hours": 8
}}"""

    print(f"\n🤖 Calling Claude AI via Databricks FMAPI...")
    print(f"   Model: claude-3-5-sonnet-20240620")
    print(f"   Request ID: {datetime.now().strftime('%Y%m%d-%H%M%S')}")

    try:
        headers = {
            "Authorization": f"Bearer {token}",
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

        start_time = datetime.now()
        response = requests.post(FMAPI_ENDPOINT, headers=headers, json=payload, timeout=30)
        end_time = datetime.now()

        response.raise_for_status()

        # Parse response
        result = response.json()
        response_text = result['choices'][0]['message']['content']

        latency = (end_time - start_time).total_seconds()

        print(f"✓ AI Response received in {latency:.2f} seconds")
        print(f"\n{'=' * 80}")
        print("🧠 CLAUDE AI GENERATED WORK ORDER")
        print(f"{'=' * 80}")

        # Extract JSON from response
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            work_order_json = response_text[json_start:json_end].strip()
        else:
            work_order_json = response_text

        try:
            work_order = json.loads(work_order_json)

            print(f"\n📋 Work Order Details:")
            print(f"   Failure Type: {work_order.get('failure_type', 'N/A')}")
            print(f"   Priority: {work_order.get('priority', 'N/A')}")
            print(f"   Predicted Failure: {work_order.get('predicted_failure_date', 'N/A')}")
            print(f"   Duration: {work_order.get('estimated_duration_hours', 'N/A')} hours")

            print(f"\n💭 AI Diagnostic Reasoning:")
            print(f"   {work_order.get('ai_repair_summary', 'N/A')}")

            print(f"\n🔧 Required Parts:")
            print(f"   {work_order.get('required_parts', 'N/A')}")

            print(f"\n{'=' * 80}")
            print(f"✅ SUCCESS: Claude AI generated a unique work order!")
            print(f"   Response ID: {result.get('id', 'N/A')}")
            print(f"   Model: {result.get('model', 'N/A')}")
            print(f"   Tokens Used: {result.get('usage', {}).get('total_tokens', 'N/A')}")
            print(f"   Timestamp: {datetime.now().isoformat()}")
            print(f"{'=' * 80}")

            # Show this is NOT mock data
            print(f"\n🎯 PROOF THIS IS REAL AI:")
            print(f"   1. Unique response ID: {result.get('id', 'N/A')}")
            print(f"   2. API latency: {latency:.2f}s (mock would be instant)")
            print(f"   3. Token usage: {result.get('usage', {}).get('total_tokens', 'N/A')} (mock has no tokens)")
            print(f"   4. Run again - you'll get a DIFFERENT response!")
            print(f"   5. Diagnostic reasoning is Claude's unique analysis")

        except json.JSONDecodeError:
            print(f"\n❌ Could not parse JSON response")
            print(f"Raw response:\n{response_text}")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ API Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Status: {e.response.status_code}")
            print(f"   Body: {e.response.text}")

    print(f"\n{'=' * 80}\n")

if __name__ == "__main__":
    generate_work_order_with_ai()
