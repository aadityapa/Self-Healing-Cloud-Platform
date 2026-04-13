import os
import uuid
from datetime import datetime, timedelta, timezone

import httpx
import pandas as pd
import streamlit as st

API_BASE = os.getenv(
    "ORCHESTRATOR_URL", "https://nexovo-helling-orchestrator.onrender.com"
)

st.set_page_config(page_title="Self-Healing Platform", layout="wide")


def inject_theme(theme: str) -> None:
    is_light = theme == "light"
    bg = (
        "radial-gradient(circle at 15% 20%, rgba(56, 189, 248, 0.20), transparent 35%),"
        "radial-gradient(circle at 85% 10%, rgba(129, 140, 248, 0.24), transparent 40%),"
        "radial-gradient(circle at 50% 80%, rgba(14, 165, 233, 0.12), transparent 45%),"
        "linear-gradient(165deg, #050816 0%, #0b1220 45%, #0b1024 100%)"
    )
    text_color = "#e2e8f0"
    card_bg = "linear-gradient(145deg, rgba(15,23,42,0.97), rgba(30,41,59,0.78))"
    border = "rgba(148, 163, 184, 0.20)"
    hero_sub = "#fcd34d"
    if is_light:
        bg = (
            "radial-gradient(circle at 10% 20%, rgba(56, 189, 248, 0.14), transparent 35%),"
            "radial-gradient(circle at 88% 12%, rgba(99, 102, 241, 0.12), transparent 40%),"
            "linear-gradient(165deg, #eff6ff 0%, #f8fafc 45%, #eef2ff 100%)"
        )
        text_color = "#0f172a"
        card_bg = "linear-gradient(145deg, rgba(255,255,255,0.92), rgba(241,245,249,0.85))"
        border = "rgba(100, 116, 139, 0.25)"
        hero_sub = "#1d4ed8"

    st.markdown(
        f"""
<style>
    .topnav {{
        position: sticky;
        top: 0;
        z-index: 99;
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 14px;
        padding: 10px 14px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 8px 24px rgba(2, 6, 23, 0.18);
    }}
    .nav-brand {{font-weight: 800; letter-spacing: 0.3px;}}
    .nav-links {{font-size: 0.88rem; opacity: 0.9;}}
    .main {{color: {text_color};}}
    .stApp {{background: {bg};}}
    .hero {{
        background: linear-gradient(135deg, rgba(245,158,11,0.20) 0%, rgba(251,191,36,0.16) 45%, rgba(56,189,248,0.10) 100%);
        border: 1px solid {border};
        border-radius: 18px;
        padding: 18px 22px;
        box-shadow: 0 20px 45px rgba(2, 6, 23, 0.25), inset 0 1px 0 rgba(255,255,255,0.06);
        backdrop-filter: blur(8px);
        margin-bottom: 14px;
    }}
    .hero-title {{
        font-size: 1.8rem;
        font-weight: 750;
        margin: 0;
        letter-spacing: 0.3px;
    }}
    .hero-sub {{
        margin-top: 6px;
        color: {hero_sub};
        font-size: 0.95rem;
    }}
    .feature-grid {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0,1fr));
        gap: 10px;
        margin: 12px 0 16px 0;
    }}
    .feature {{
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 14px;
        padding: 10px 12px;
        box-shadow: 0 14px 28px rgba(2, 6, 23, 0.16);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }}
    .feature:hover {{
        transform: translateY(-4px);
        box-shadow: 0 18px 32px rgba(2, 6, 23, 0.24);
    }}
    div[data-testid="stMetric"] {{
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 14px;
        padding: 12px;
        box-shadow: 0 16px 30px rgba(2, 6, 23, 0.20), inset 0 1px 0 rgba(255,255,255,0.04);
    }}
    .card {{
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 14px;
        padding: 14px;
        margin-bottom: 12px;
        box-shadow: 0 14px 28px rgba(2, 6, 23, 0.18), inset 0 1px 0 rgba(255,255,255,0.04);
        backdrop-filter: blur(8px);
    }}
    .sev-critical {{color: #ef4444; font-weight: 700;}}
    .sev-high {{color: #f97316; font-weight: 700;}}
    .sev-medium {{color: #eab308; font-weight: 700;}}
    .sev-low {{color: #22c55e; font-weight: 700;}}
    .tiny {{color: #60a5fa; font-size: 0.84rem; margin-top: 4px;}}
    .node-wrap {{height: 130px; margin-bottom: 8px;}}
    .node-svg circle {{animation: pulse 3.6s ease-in-out infinite;}}
    .node-svg line {{stroke-dasharray: 4 5; animation: move 7s linear infinite;}}
    .cloud-3d {{
        width: 120px;
        height: 120px;
        margin: 4px auto 10px auto;
        border-radius: 50%;
        background: radial-gradient(circle at 30% 30%, #7dd3fc, #2563eb 55%, #1e293b 100%);
        box-shadow: inset -12px -12px 24px rgba(2,6,23,0.35), inset 10px 12px 18px rgba(255,255,255,0.24), 0 20px 34px rgba(2,6,23,0.40);
        animation: spinCloud 12s linear infinite;
        transform-style: preserve-3d;
    }}
    .steps {{
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 14px;
        padding: 12px 14px;
        margin-bottom: 10px;
    }}
    .steps b {{color: #fbbf24;}}
    .selling-grid {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0,1fr));
        gap: 12px;
        margin: 12px 0 18px 0;
    }}
    .plan {{
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 16px;
        padding: 14px;
        box-shadow: 0 14px 26px rgba(2, 6, 23, 0.18);
        transition: transform 0.22s ease, border-color 0.22s ease;
    }}
    .plan:hover {{transform: translateY(-5px); border-color: #f59e0b;}}
    .plan-price {{font-size: 1.35rem; font-weight: 800; margin-top: 6px;}}
    .chip {{
        display: inline-block;
        border: 1px solid #f59e0b;
        color: #f59e0b;
        border-radius: 999px;
        padding: 2px 8px;
        font-size: 0.72rem;
        margin-left: 6px;
        vertical-align: middle;
    }}
    .cta {{
        background: linear-gradient(90deg, #f59e0b, #f97316, #0ea5e9);
        background-size: 240% 240%;
        color: white;
        border-radius: 12px;
        padding: 10px 14px;
        font-weight: 700;
        text-align: center;
        margin: 10px 0 0 0;
        animation: shift 6s ease infinite;
        box-shadow: 0 14px 25px rgba(37, 99, 235, 0.4);
    }}
    @keyframes pulse {{0%,100% {{transform: scale(1); opacity: 0.8;}} 50% {{transform: scale(1.08); opacity: 1;}}}}
    @keyframes move {{from {{stroke-dashoffset: 0;}} to {{stroke-dashoffset: 60;}}}}
    @keyframes spinCloud {{from {{transform: rotateY(0deg) rotateX(6deg);}} to {{transform: rotateY(360deg) rotateX(6deg);}}}}
    @keyframes shift {{0% {{background-position: 0% 50%;}} 50% {{background-position: 100% 50%;}} 100% {{background-position: 0% 50%;}}}}
</style>
""",
        unsafe_allow_html=True,
    )


def gauge(label: str, value: float, max_value: float = 100.0) -> None:
    pct = 0.0 if max_value == 0 else max(0.0, min(100.0, (value / max_value) * 100.0))
    color = "#22c55e"
    if pct >= 70:
        color = "#f59e0b"
    if pct >= 90:
        color = "#ef4444"
    st.markdown(
        f"""
<div class='card'>
  <b>{label}</b>
  <div style='margin-top:8px;height:10px;border-radius:999px;background:#334155;overflow:hidden;'>
    <div style='width:{pct:.1f}%;height:10px;background:{color};box-shadow:0 0 12px {color};'></div>
  </div>
  <div class='tiny' style='margin-top:6px;'>{value:.1f}% utilization</div>
</div>
""",
        unsafe_allow_html=True,
    )

with st.sidebar:
    st.markdown("## Control Center")
    if st.button("Refresh now", use_container_width=True):
        st.rerun()
    theme_mode = st.selectbox("Theme", ["dark", "light"], index=0)
    auto_refresh = st.toggle("Auto refresh (15s)", value=False)
    selected_service = st.text_input("Filter service", value="")
    selected_severity = st.selectbox(
        "Filter severity", ["all", "critical", "high", "medium", "low"], index=0
    )
    selected_window = st.selectbox(
        "Time window", ["last_1h", "last_6h", "last_24h", "last_7d", "all_time"], index=2
    )
    only_open = st.toggle("Only unacknowledged incidents", value=False)
    show_marketing = st.toggle("Show SaaS hero section", value=True)
    st.markdown("---")
    st.caption("Use this panel to tune views and run scenario simulations.")

inject_theme(theme_mode)
if auto_refresh:
    st.caption("Auto refresh enabled. Click 'Refresh now' every few seconds.")

st.markdown(
    """
<div class='topnav'>
  <div class='nav-brand'>NEXOVO HELLING CLOUD</div>
  <div class='nav-links'>Platform | AI Engine | Security | Pricing | Docs</div>
</div>
""",
    unsafe_allow_html=True,
)

if show_marketing:
    st.markdown(
        """
<div class='hero'>
  <p class='hero-title'>Nexovo Helling Cloud Platform</p>
  <p class='hero-sub'>Building scalable digital systems for the next generation.</p>
</div>
<div class='cloud-3d'></div>
<div class='node-wrap'>
  <svg class='node-svg' viewBox='0 0 960 140' width='100%' height='130' xmlns='http://www.w3.org/2000/svg'>
    <line x1='80' y1='70' x2='280' y2='40' stroke='#38bdf8' stroke-width='2'/>
    <line x1='280' y1='40' x2='480' y2='72' stroke='#818cf8' stroke-width='2'/>
    <line x1='480' y1='72' x2='690' y2='38' stroke='#22d3ee' stroke-width='2'/>
    <line x1='480' y1='72' x2='850' y2='94' stroke='#38bdf8' stroke-width='2'/>
    <circle cx='80' cy='70' r='11' fill='#0ea5e9'/>
    <circle cx='280' cy='40' r='12' fill='#6366f1'/>
    <circle cx='480' cy='72' r='14' fill='#22d3ee'/>
    <circle cx='690' cy='38' r='11' fill='#0ea5e9'/>
    <circle cx='850' cy='94' r='12' fill='#6366f1'/>
  </svg>
</div>
<div class='feature-grid'>
  <div class='feature'><b>Real-Time Intelligence</b><br/>Actionable signal detection for smarter decisions.</div>
  <div class='feature'><b>AI RCA</b><br/>Correlate metrics, logs, and events in seconds.</div>
  <div class='feature'><b>Seamless Integration</b><br/>Connect your stack and automate every workflow.</div>
  <div class='feature'><b>Measurable Impact</b><br/>Track remediation success and operational ROI.</div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown(
        """
<div class='selling-grid'>
  <div class='plan'>
    <b>Starter Ops</b>
    <div class='plan-price'>$49<span style='font-size:0.8rem;'>/mo</span></div>
    Best for small teams building AI-assisted incident response.
  </div>
  <div class='plan'>
    <b>Growth SRE <span class='chip'>Most Popular</span></b>
    <div class='plan-price'>$199<span style='font-size:0.8rem;'>/mo</span></div>
    Full anomaly + RCA + safe auto-remediation workflow.
  </div>
  <div class='plan'>
    <b>Enterprise Autonomous</b>
    <div class='plan-price'>Custom</div>
    Multi-cluster, policy guardrails, and dedicated reliability advisory.
  </div>
</div>
<div class='cta'>Book a Strategy Call | Scale with Nexovo</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown(
        """
<div class='steps'>
  <b>How it works:</b><br/>
  1) Observe metrics/logs/events -> 2) Detect anomaly -> 3) RCA hypothesis -> 4) Safe remediation -> 5) Learn and improve
</div>
""",
        unsafe_allow_html=True,
    )


def get_json(path: str):
    return httpx.get(f"{API_BASE}{path}", timeout=10.0).json()


def check_backend_online() -> bool:
    try:
        resp = httpx.get(f"{API_BASE}/health", timeout=8.0)
        if resp.status_code == 200:
            return True
    except Exception:
        pass
    try:
        # Fallback probe because some hosted free-tier setups may intermittently
        # return 404 on /health during cold starts while API routes are available.
        resp = httpx.get(f"{API_BASE}/v1/incidents", timeout=8.0)
        return resp.status_code == 200
    except Exception:
        return False


def synthetic_incident(service: str, namespace: str, cpu: int, memory: int, error_rate: float, latency: int):
    sev = "low"
    if error_rate > 5 or latency > 850:
        sev = "critical"
    elif error_rate > 3 or cpu > 90 or memory > 90:
        sev = "high"
    elif error_rate > 1.5 or latency > 450:
        sev = "medium"
    return {
        "id": str(uuid.uuid4()),
        "service": service,
        "severity": sev,
        "confidence": min(0.99, max(0.2, (error_rate + cpu / 30.0) / 10.0)),
        "hypothesis": "Simulated RCA: probable saturation or dependency latency.",
        "recommended_action": "scale_deployment" if cpu > 90 else "restart_pod",
        "executed": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "metadata": {
            "namespace": namespace,
            "cpu": f"{cpu:.2f}",
            "memory": f"{memory:.2f}",
            "error_rate": f"{error_rate:.2f}",
            "latency_ms": f"{latency:.2f}",
        },
    }


def incident_runbook(incident: dict) -> list[str]:
    severity = incident.get("severity", "low")
    action = incident.get("recommended_action", "notify_human")
    service = incident.get("service", "service")
    steps = [
        f"Validate impacted service `{service}` and confirm scope in namespace.",
        "Check last deployment and configuration changes in previous 30 minutes.",
        "Correlate p95 latency, error-rate, and pod health to confirm root cause.",
    ]
    if action == "rollback_deployment":
        steps.append("Trigger rollback to previous stable version and monitor 5-minute SLO recovery.")
    elif action == "scale_deployment":
        steps.append("Scale replicas and verify queue depth and CPU return below saturation thresholds.")
    elif action == "restart_pod":
        steps.append("Restart unhealthy pods in rolling manner and verify no spike in 5xx responses.")
    else:
        steps.append("Escalate to on-call engineer and capture diagnostics bundle.")
    if severity in {"high", "critical"}:
        steps.append("Open incident bridge, assign incident commander, and post updates every 10 minutes.")
    return steps


def reliability_score(incidents_count: int, critical_count: int, success_rate: float) -> float:
    base = 100.0
    penalty = (incidents_count * 1.2) + (critical_count * 4.0) + ((100.0 - success_rate) * 0.2)
    return max(0.0, min(100.0, base - penalty))


def in_selected_window(iso_timestamp: str, window: str) -> bool:
    if window == "all_time":
        return True
    if not iso_timestamp:
        return False
    try:
        event_time = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta_map = {
            "last_1h": timedelta(hours=1),
            "last_6h": timedelta(hours=6),
            "last_24h": timedelta(hours=24),
            "last_7d": timedelta(days=7),
        }
        return event_time >= (now - delta_map.get(window, timedelta(hours=24)))
    except Exception:
        return True


status_col, _, endpoint_col = st.columns([1, 0.2, 2])
demo_mode = False
with status_col:
    if check_backend_online():
        health = {"status": "ok"}
        st.success("Orchestrator Online")
    else:
        health = {"status": "unreachable"}
        demo_mode = True
        st.warning("Orchestrator Offline (Dashboard running in demo mode)")
        st.caption(
            "To switch to live mode, deploy orchestrator API on Render and set Streamlit secret `ORCHESTRATOR_URL` to that public URL."
        )
with endpoint_col:
    st.markdown(
        f"<div class='card'><b>Connected API:</b> {API_BASE}<br><b>Status:</b> {health.get('status', 'unknown')}<div class='tiny'>Live AI remediation control plane link active.</div></div>",
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

if demo_mode and "demo_incidents" not in st.session_state:
    st.session_state["demo_incidents"] = []
if demo_mode and "demo_actions" not in st.session_state:
    st.session_state["demo_actions"] = []
if demo_mode:
    incidents = st.session_state["demo_incidents"]
    actions = st.session_state["demo_actions"]

incidents = [i for i in incidents if in_selected_window(i.get("created_at", ""), selected_window)]
actions = [a for a in actions if in_selected_window(a.get("created_at", ""), selected_window)]

if selected_service.strip():
    incidents = [i for i in incidents if i.get("service", "").lower() == selected_service.strip().lower()]

if selected_severity != "all":
    incidents = [i for i in incidents if i.get("severity") == selected_severity]

if only_open:
    incidents = [
        i for i in incidents if i.get("metadata", {}).get("acknowledged", "false").lower() != "true"
    ]

crit_count = sum(1 for i in incidents if i.get("severity") == "critical")
success_count = sum(1 for a in actions if a.get("success"))
success_rate = (success_count / len(actions) * 100) if actions else 0.0

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Active Incidents", len(incidents))
kpi2.metric("Critical Incidents", crit_count)
kpi3.metric("Remediation Actions", len(actions))
kpi4.metric("Action Success Rate", f"{success_rate:.1f}%")

if incidents:
    tdf = pd.DataFrame(incidents)[["created_at", "severity", "confidence"]].copy()
    tdf["created_at"] = pd.to_datetime(tdf["created_at"], errors="coerce")
    tdf = tdf.dropna(subset=["created_at"]).sort_values("created_at")
    if not tdf.empty:
        tdf["incident_count"] = 1
        tdf["critical_count"] = (tdf["severity"] == "critical").astype(int)
        trend = tdf.set_index("created_at")[["incident_count", "critical_count", "confidence"]]
        st.markdown("#### KPI Trends")
        st.line_chart(trend)

cpu_avg = 0.0
mem_avg = 0.0
err_avg = 0.0
if incidents:
    cpu_vals = [float(i.get("metadata", {}).get("cpu", 0.0)) for i in incidents if i.get("metadata")]
    mem_vals = [float(i.get("metadata", {}).get("memory", 0.0)) for i in incidents if i.get("metadata")]
    err_vals = [float(i.get("metadata", {}).get("error_rate", 0.0)) for i in incidents if i.get("metadata")]
    cpu_avg = sum(cpu_vals) / len(cpu_vals) if cpu_vals else 0.0
    mem_avg = sum(mem_vals) / len(mem_vals) if mem_vals else 0.0
    err_avg = sum(err_vals) / len(err_vals) if err_vals else 0.0

g1, g2, g3 = st.columns(3)
with g1:
    gauge("CPU Load Gauge", cpu_avg)
with g2:
    gauge("Memory Load Gauge", mem_avg)
with g3:
    gauge("Error Rate Gauge", err_avg, max_value=20.0)

left, right = st.columns([2.2, 1.2], gap="large")

with right:
    st.markdown("### Simulate Production Signal")
    st.caption("Use this simulator to mimic real incidents and watch automated RCA/action flow.")
    st.caption("Tip: set CPU > 90 and Error Rate > 5 to emulate high-severity incidents.")
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
            if demo_mode:
                incident = synthetic_incident(
                    service=service,
                    namespace=namespace,
                    cpu=cpu,
                    memory=memory,
                    error_rate=error_rate,
                    latency=latency,
                )
                action = {
                    "action": incident["recommended_action"],
                    "success": True,
                    "message": "Demo mode remediation executed locally in dashboard.",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                st.session_state["demo_incidents"] = [incident] + st.session_state["demo_incidents"]
                st.session_state["demo_actions"] = [action] + st.session_state["demo_actions"]
                st.success("Demo signal processed (no backend needed).")
                with st.expander("Detection Response", expanded=True):
                    st.json({"incident": incident, "action_result": action, "mode": "demo"})
            else:
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
                "id",
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

        sev_df = (
            pd.DataFrame(incidents)["severity"]
            .value_counts()
            .rename_axis("severity")
            .reset_index(name="count")
        )
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.markdown("#### Severity Distribution")
            st.bar_chart(sev_df.set_index("severity"))
        with chart_col2:
            st.markdown("#### Confidence Trend")
            conf_df = pd.DataFrame(incidents)[["created_at", "confidence"]].copy()
            conf_df["created_at"] = pd.to_datetime(conf_df["created_at"], errors="coerce")
            conf_df = conf_df.sort_values("created_at")
            conf_df = conf_df.set_index("created_at")
            st.line_chart(conf_df)

        latest = incidents[0]
        sev = latest.get("severity", "low")
        st.markdown(
            f"<div class='card'><b>Latest RCA:</b> {latest.get('hypothesis', 'n/a')}<br><b>Severity:</b> <span class='sev-{sev}'>{sev.upper()}</span><br><b>Recommended Action:</b> {latest.get('recommended_action', 'n/a')}</div>",
            unsafe_allow_html=True,
        )

        st.markdown("### Incident Drill-down")
        incident_options = {
            f"{item.get('service','unknown')} | {item.get('severity','low')} | {item.get('id','')}": item
            for item in incidents[:25]
        }
        selected_key = st.selectbox("Select incident", list(incident_options.keys()))
        selected_incident = incident_options[selected_key]
        action_col1, action_col2 = st.columns(2)
        with action_col1:
            if st.button("Acknowledge Incident", use_container_width=True):
                if demo_mode:
                    selected_incident.setdefault("metadata", {})["acknowledged"] = "true"
                    st.success("Incident acknowledged in demo mode.")
                else:
                    try:
                        r = httpx.post(
                            f"{API_BASE}/v1/incidents/{selected_incident.get('id')}/ack", timeout=10.0
                        )
                        r.raise_for_status()
                        st.success("Incident acknowledged.")
                    except Exception as exc:
                        st.error(f"Acknowledge failed: {exc}")
        with action_col2:
            if st.button("Escalate to On-call", use_container_width=True):
                if demo_mode:
                    selected_incident.setdefault("metadata", {})["escalated"] = "true"
                    selected_incident["metadata"]["escalated_to"] = "sre-oncall"
                    st.warning("Incident escalated in demo mode.")
                else:
                    try:
                        r = httpx.post(
                            f"{API_BASE}/v1/incidents/{selected_incident.get('id')}/escalate", timeout=10.0
                        )
                        r.raise_for_status()
                        st.warning("Incident escalated to on-call.")
                    except Exception as exc:
                        st.error(f"Escalation failed: {exc}")
        with st.expander("Detailed incident context", expanded=True):
            st.json(selected_incident)
    else:
        st.info("No incidents yet. Send a signal from the right panel.")

    st.markdown("### Remediation Timeline")
    if actions:
        adf = pd.DataFrame(actions)[["action", "success", "message", "created_at"]]
        adf["success"] = adf["success"].map(lambda x: "Success" if x else "Blocked")
        st.dataframe(adf, use_container_width=True, hide_index=True)
        action_stats = pd.DataFrame(actions)["action"].value_counts().reset_index()
        action_stats.columns = ["action", "count"]
        st.markdown("#### Action Mix")
        st.area_chart(action_stats.set_index("action"))
    else:
        st.info("No remediation actions recorded yet.")

st.markdown("## Operations Intelligence Toolkit")
ops_tab, runbook_tab, planner_tab, architecture_tab = st.tabs(
    ["Service Intelligence", "Runbook Assistant", "Scenario Planner", "Architecture Map"]
)

with ops_tab:
    if incidents:
        idf = pd.DataFrame(incidents)
        if "created_at" in idf.columns:
            idf["created_at"] = pd.to_datetime(idf["created_at"], errors="coerce")
        svc = (
            idf.groupby("service", as_index=False)
            .agg(
                incidents=("id", "count"),
                avg_confidence=("confidence", "mean"),
                critical=("severity", lambda s: int((s == "critical").sum())),
            )
            .sort_values(["incidents", "critical"], ascending=False)
        )
        svc["avg_confidence"] = svc["avg_confidence"].fillna(0.0).map(lambda x: round(float(x), 2))
        st.markdown("### Service Leaderboard")
        st.dataframe(svc, use_container_width=True, hide_index=True)

        left_ops, right_ops = st.columns(2)
        with left_ops:
            st.markdown("#### Incident Volume by Service")
            st.bar_chart(svc.set_index("service")[["incidents"]])
        with right_ops:
            st.markdown("#### Critical Incidents by Service")
            st.bar_chart(svc.set_index("service")[["critical"]])
    else:
        st.info("No incidents available for service intelligence yet.")

    export_col1, export_col2 = st.columns(2)
    with export_col1:
        if incidents:
            incident_csv = pd.DataFrame(incidents).to_csv(index=False)
            st.download_button(
                "Export Incidents CSV",
                data=incident_csv,
                file_name="nexovo_incidents.csv",
                mime="text/csv",
                use_container_width=True,
            )
    with export_col2:
        if actions:
            action_csv = pd.DataFrame(actions).to_csv(index=False)
            st.download_button(
                "Export Actions CSV",
                data=action_csv,
                file_name="nexovo_actions.csv",
                mime="text/csv",
                use_container_width=True,
            )

with runbook_tab:
    st.markdown("### AI-Guided Incident Runbook")
    if incidents:
        runbook_options = {
            f"{item.get('service','unknown')} | {item.get('severity','low')} | {item.get('id','')}": item
            for item in incidents[:25]
        }
        rb_key = st.selectbox("Choose incident for runbook", list(runbook_options.keys()))
        rb_incident = runbook_options[rb_key]
        steps = incident_runbook(rb_incident)
        for idx, step in enumerate(steps, start=1):
            st.markdown(f"{idx}. {step}")
        st.code(
            f"RCA: {rb_incident.get('hypothesis', 'N/A')}\n"
            f"Recommended Action: {rb_incident.get('recommended_action', 'N/A')}\n"
            f"Confidence: {rb_incident.get('confidence', 0):.2f}"
        )
    else:
        st.info("Generate or ingest incidents to enable runbook assistant.")

with planner_tab:
    st.markdown("### Capacity and Risk Planner")
    p_col1, p_col2, p_col3 = st.columns(3)
    with p_col1:
        projected_qps = st.slider("Projected QPS spike (%)", 0, 300, 80)
    with p_col2:
        current_error = st.slider("Current error rate (%)", 0.0, 20.0, 2.0)
    with p_col3:
        headroom = st.slider("Infra headroom (%)", 0, 100, 35)

    risk_score = (projected_qps * 0.45) + (current_error * 8.0) - (headroom * 0.4)
    risk_score = max(0.0, min(100.0, risk_score))
    st.metric("Predicted Incident Risk", f"{risk_score:.1f}%")
    if risk_score >= 70:
        st.error("High projected risk. Prepare scale-up + rollback guardrails.")
    elif risk_score >= 40:
        st.warning("Moderate risk. Recommend canary release and tighter alerting.")
    else:
        st.success("Risk is manageable under current assumptions.")

    rel = reliability_score(len(incidents), crit_count, success_rate)
    st.metric("Platform Reliability Score", f"{rel:.1f}/100")
    st.caption("Score combines incident load, critical events, and remediation success rate.")

with architecture_tab:
    st.markdown("### Self-Healing System Map")
    st.graphviz_chart(
        """
digraph G {
    rankdir=LR;
    node [shape=box, style=rounded];
    Traffic -> "Kubernetes Services";
    "Kubernetes Services" -> Prometheus;
    "Kubernetes Services" -> "Log Pipeline";
    Prometheus -> "Detection Engine";
    "Log Pipeline" -> "RCA Correlator";
    "Detection Engine" -> "Decision Engine";
    "RCA Correlator" -> "Decision Engine";
    "Decision Engine" -> "Remediation Executor";
    "Remediation Executor" -> "Kubernetes Services";
    "Decision Engine" -> "Nexovo Dashboard";
}
"""
    )
    st.markdown("### SLO Snapshot")
    slo_df = pd.DataFrame(
        [
            {"SLI": "Availability", "Target": "99.9%", "Current": "99.7%"},
            {"SLI": "p95 Latency", "Target": "< 250ms", "Current": "232ms"},
            {"SLI": "Error Rate", "Target": "< 1.0%", "Current": "0.8%"},
            {"SLI": "MTTR", "Target": "< 15 min", "Current": "11 min"},
        ]
    )
    st.dataframe(slo_df, use_container_width=True, hide_index=True)
