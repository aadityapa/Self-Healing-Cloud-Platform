import os
from datetime import datetime, timezone

import httpx
import pandas as pd
import streamlit as st

API_BASE = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")

st.set_page_config(page_title="Self-Healing Platform", layout="wide")
st.markdown(
    """
<style>
    .main {background: linear-gradient(180deg, #0b1220 0%, #0f172a 100%); color: #e2e8f0;}
    .stApp {background: linear-gradient(180deg, #0b1220 0%, #0f172a 100%);}
    div[data-testid="stMetric"] {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 14px;
        padding: 10px;
    }
    .card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 14px;
        padding: 14px;
        margin-bottom: 12px;
    }
    .sev-critical {color: #ef4444; font-weight: 700;}
    .sev-high {color: #f97316; font-weight: 700;}
    .sev-medium {color: #eab308; font-weight: 700;}
    .sev-low {color: #22c55e; font-weight: 700;}
</style>
""",
    unsafe_allow_html=True,
)

st.title("Self-Healing Cloud Platform")
st.caption("AI-driven operations console for incident detection, RCA, and automated remediation.")


def get_json(path: str):
    return httpx.get(f"{API_BASE}{path}", timeout=10.0).json()


status_col, _, endpoint_col = st.columns([1, 0.2, 2])
with status_col:
    try:
        health = get_json("/health")
        st.success("Orchestrator Online")
    except Exception:
        health = {"status": "unreachable"}
        st.error("Orchestrator Offline")
with endpoint_col:
    st.markdown(
        f"<div class='card'><b>Connected API:</b> {API_BASE}<br><b>Status:</b> {health.get('status', 'unknown')}</div>",
        unsafe_allow_html=True,
    )

try:
    incidents = get_json("/v1/incidents")
except Exception:
    incidents = []

try:
    actions = get_json("/v1/actions")
except Exception:
    actions = []

crit_count = sum(1 for i in incidents if i.get("severity") == "critical")
success_count = sum(1 for a in actions if a.get("success"))
success_rate = (success_count / len(actions) * 100) if actions else 0.0

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Active Incidents", len(incidents))
kpi2.metric("Critical Incidents", crit_count)
kpi3.metric("Remediation Actions", len(actions))
kpi4.metric("Action Success Rate", f"{success_rate:.1f}%")

left, right = st.columns([2.2, 1.2], gap="large")

with right:
    st.markdown("### Simulate Production Signal")
    with st.container(border=True):
        service = st.text_input("Service", value="checkout-service")
        namespace = st.text_input("Namespace", value="prod")
        cpu = st.slider("CPU %", 1, 100, 78)
        memory = st.slider("Memory %", 1, 100, 72)
        error_rate = st.slider("Error Rate %", 0.0, 20.0, 2.2)
        latency = st.slider("p95 Latency (ms)", 30, 2000, 460)
        log_errors = st.slider("Log Error Count", 0, 250, 22)
        deploy_changed = st.checkbox("Deployment changed in last 15m", value=False)

        if st.button("Run Detection and Remediation", type="primary", use_container_width=True):
            payload = {
                "service": service,
                "namespace": namespace,
                "cpu": cpu,
                "memory": memory,
                "error_rate": error_rate,
                "p95_latency_ms": latency,
                "log_error_count": log_errors,
                "deploy_changed_last_15m": deploy_changed,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            try:
                resp = httpx.post(f"{API_BASE}/v1/detect", json=payload, timeout=10.0)
                resp.raise_for_status()
                data = resp.json()
                st.success("Signal processed successfully.")
                with st.expander("Detection Response", expanded=True):
                    st.json(data)
            except Exception as exc:
                st.error(f"Failed to call orchestrator: {exc}")

with left:
    st.markdown("### Incident Feed")
    if incidents:
        df = pd.DataFrame(incidents)[
            [
                "service",
                "severity",
                "confidence",
                "hypothesis",
                "recommended_action",
                "executed",
                "created_at",
            ]
        ]
        df["confidence"] = df["confidence"].map(lambda x: f"{x:.2f}")
        st.dataframe(df, use_container_width=True, hide_index=True)

        latest = incidents[0]
        sev = latest.get("severity", "low")
        st.markdown(
            f"<div class='card'><b>Latest RCA:</b> {latest.get('hypothesis', 'n/a')}<br><b>Severity:</b> <span class='sev-{sev}'>{sev.upper()}</span><br><b>Recommended Action:</b> {latest.get('recommended_action', 'n/a')}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.info("No incidents yet. Send a signal from the right panel.")

    st.markdown("### Remediation Timeline")
    if actions:
        adf = pd.DataFrame(actions)[["action", "success", "message", "created_at"]]
        adf["success"] = adf["success"].map(lambda x: "Success" if x else "Blocked")
        st.dataframe(adf, use_container_width=True, hide_index=True)
    else:
        st.info("No remediation actions recorded yet.")
