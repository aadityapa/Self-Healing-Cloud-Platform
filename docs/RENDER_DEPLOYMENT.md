# Render Deployment Guide

This deploys the orchestrator API and connects Streamlit Cloud to live mode.

## 1) Deploy Orchestrator on Render

1. Open Render dashboard.
2. Click **New +** -> **Blueprint**.
3. Connect this GitHub repo.
4. Render detects `render.yaml` and creates:
   - `nexovo-helling-orchestrator`
5. Click **Apply** and wait for deploy.

Health endpoint after deploy:

- `https://<your-render-service>.onrender.com/health`

## 2) Connect Streamlit to Orchestrator

In Streamlit Cloud app settings -> **Secrets**, add:

```toml
ORCHESTRATOR_URL = "https://<your-render-service>.onrender.com"
```

Then reboot/redeploy Streamlit app.

## 3) Validate Live Mode

- Warning banner for demo mode disappears.
- Dashboard status shows orchestrator online.
- `Run Detection and Remediation` uses live API instead of synthetic demo responses.
