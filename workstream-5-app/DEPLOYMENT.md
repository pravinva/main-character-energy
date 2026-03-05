# Databricks App Deployment Guide

## Prerequisites

1. Databricks CLI installed and authenticated
2. Access to Databricks workspace: `fe-sandbox-serverless-sandbox-tladem.cloud.databricks.com`
3. Profile configured: `fe-vm`

## Setup Secrets

Before deploying, create a secret scope and add the OAuth token:

```bash
# Create secret scope (if not exists)
databricks secrets create-scope mce-secrets --profile fe-vm

# Add OAuth token
databricks secrets put-secret mce-secrets lakebase-oauth-token --profile fe-vm
# Paste your OAuth token when prompted
```

## Build Frontend

```bash
cd frontend
npm install
npm run build
```

This creates the production bundle in `frontend/dist/`

## Deploy to Databricks Apps

```bash
cd /Users/pravin.varma/Documents/Demo/main-character-energy/workstream-5-app
databricks apps deploy --profile fe-vm
```

## Local Development

### Backend

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set OAuth token
export LAKEBASE_OAUTH_TOKEN='your-oauth-token-here'

# Run server
uvicorn app:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev  # Runs on http://localhost:3000
```

## Environment Variables

### Backend
- `LAKEBASE_OAUTH_TOKEN` (required): OAuth token for Lakebase authentication
- `DATABRICKS_HOST` (optional): Databricks workspace URL

### Frontend
- `VITE_API_BASE_URL` (optional): Backend API URL (defaults to `/api`)

## Lakebase Setup

If tables don't exist, run the setup scripts:

```bash
cd backend

# Set OAuth token
export PGPASSWORD='your-oauth-token-here'

# Create tables
./setup_lakebase.sh

# Seed sample data
./seed_sample_data.sh
```

## Verify Deployment

1. Check app status:
```bash
databricks apps list --profile fe-vm
```

2. Get app URL:
```bash
databricks apps get mce-field-operations --profile fe-vm
```

3. Test endpoints:
```bash
curl https://your-app-url.cloud.databricks.com/api/health
curl https://your-app-url.cloud.databricks.com/api/dashboard-stats
```

## Troubleshooting

### Secret Not Found
If deployment fails with "Secret not found":
```bash
databricks secrets list-secrets mce-secrets --profile fe-vm
```

### OAuth Token Expired
Update the token:
```bash
databricks secrets put-secret mce-secrets lakebase-oauth-token --profile fe-vm
```

### Frontend Not Loading
Check that `frontend/dist` exists:
```bash
ls -la frontend/dist
```

If missing, rebuild:
```bash
cd frontend && npm run build
```

## Architecture

```
┌─────────────────────────────────────┐
│  Databricks Apps (Serverless)       │
│                                      │
│  ├─ Frontend (Static)                │
│  │  └─ React + TypeScript            │
│  │     Location: frontend/dist/      │
│  │                                    │
│  └─ Backend (Python 3.11)            │
│     └─ FastAPI + uvicorn             │
│        Port: 8000                    │
│        Endpoints: /api/*             │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│  Lakebase (Serverless Postgres)     │
│  Instance: b77ccee1-1d75-4ab9        │
│  Database: databricks_postgres       │
│  Schema: mce_operations              │
└─────────────────────────────────────┘
```

## Resources

- Databricks Apps Docs: https://docs.databricks.com/en/dev-tools/databricks-apps/
- Lakebase Docs: https://docs.databricks.com/en/lakehouse-federation/lakebase.html
