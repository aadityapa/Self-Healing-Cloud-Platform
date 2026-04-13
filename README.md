# Self-Healing Cloud Platform (Enterprise Starter)

Production-style starter for an AI-driven self-healing platform.

## Included Components

- `orchestrator` (FastAPI): anomaly detection + policy decision + remediation simulator
- `dashboard` (Streamlit): production-style operations console UI
- `prometheus`: scrapes orchestrator metrics endpoint
- Dockerized, network-ready (`0.0.0.0` bindings)

## Quick Start (Local - Recommended on your machine)

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-deps.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\start-platform.ps1
```

Local URLs:

- API: `http://localhost:8000`
- Dashboard: `http://localhost:8501`

To stop:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\stop-platform.ps1
```

## Quick Start (Docker, optional)

```powershell
docker compose up --build -d
```

URLs:

- API: `http://localhost:8000`
- Dashboard: `http://localhost:8501`
- Prometheus: `http://localhost:9090`

To get LAN URLs (same network):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\get-lan-url.ps1
```

## Test Detection API

```powershell
$payload = @{
  service = "checkout-service"
  namespace = "prod"
  cpu = 96
  memory = 91
  error_rate = 6.2
  p95_latency_ms = 940
  log_error_count = 130
  deploy_changed_last_15m = $true
} | ConvertTo-Json

Invoke-RestMethod -Method POST -Uri "http://localhost:8000/v1/detect" -Body $payload -ContentType "application/json"
```

## Local Run Without Docker

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-local.ps1
```

## Publish to GitHub (Make this your linked project)

1) Initialize local git repo:

```powershell
git init
git add .
git commit -m "Initial commit: self-healing cloud platform starter"
```

2) Create an empty repo on GitHub, then link and push:

```powershell
git remote add origin https://github.com/<your-username>/<your-repo-name>.git
git branch -M main
git push -u origin main
```

After push, this folder is linked to your GitHub project.

## Repository Standards Included

- `LICENSE` (MIT)
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `.github/workflows/ci.yml`
- `.github/pull_request_template.md`
- `.github/ISSUE_TEMPLATE/*`

## Next Enterprise Steps

- Add Kafka + Flink streaming feature pipeline
- Add Elasticsearch + Logstash ingestion
- Replace remediation simulator with Kubernetes operator actions
- Add model registry, retraining, and evaluation pipeline
