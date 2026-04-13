from typing import Dict, List

from fastapi import FastAPI, HTTPException
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest
from starlette.responses import Response

from .engine import DetectionEngine, PolicyEngine, RemediationEngine, StateStore
from .models import ActionResult, DetectionResponse, Incident, SignalWindow

app = FastAPI(title="Self-Healing Orchestrator", version="1.0.0")

state = StateStore()
detector = DetectionEngine()
policy = PolicyEngine()
remediator = RemediationEngine()

INCIDENTS_TOTAL = Counter("shp_incidents_total", "Total incidents", ["service", "severity"])
REMEDIATIONS_TOTAL = Counter(
    "shp_remediations_total", "Total remediation executions", ["action", "success"]
)
ANOMALY_SCORE = Gauge("shp_anomaly_score", "Latest anomaly score", ["service"])


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/v1/detect", response_model=DetectionResponse)
def detect_and_heal(signal: SignalWindow) -> DetectionResponse:
    score, is_anomaly = detector.predict(signal)
    ANOMALY_SCORE.labels(service=signal.service).set(score)

    if not is_anomaly and signal.error_rate < 2 and signal.p95_latency_ms < 400:
        return DetectionResponse(
            incident=None,
            action_result=None,
            reasons=["Within normal baseline and no threshold breach"],
        )

    decision = policy.decide(signal, score)
    incident = decision.incident
    if incident is None:
        return decision

    result = remediator.execute(incident)
    incident.executed = result.success

    with state.lock:
        state.incidents.insert(0, incident)
        state.actions.insert(0, result)

    INCIDENTS_TOTAL.labels(service=incident.service, severity=incident.severity.value).inc()
    REMEDIATIONS_TOTAL.labels(
        action=result.action.value, success=str(result.success).lower()
    ).inc()

    decision.action_result = result
    return decision


@app.get("/v1/incidents", response_model=List[Incident])
def list_incidents() -> List[Incident]:
    return state.incidents[:100]


@app.get("/v1/actions", response_model=List[ActionResult])
def list_actions() -> List[ActionResult]:
    return state.actions[:100]


def _get_incident_or_404(incident_id: str) -> Incident:
    for incident in state.incidents:
        if incident.id == incident_id:
            return incident
    raise HTTPException(status_code=404, detail="Incident not found")


@app.post("/v1/incidents/{incident_id}/ack")
def acknowledge_incident(incident_id: str) -> Dict[str, str]:
    with state.lock:
        incident = _get_incident_or_404(incident_id)
        incident.metadata["acknowledged"] = "true"
    return {"status": "ok", "message": f"Incident {incident_id} acknowledged"}


@app.post("/v1/incidents/{incident_id}/escalate")
def escalate_incident(incident_id: str) -> Dict[str, str]:
    with state.lock:
        incident = _get_incident_or_404(incident_id)
        incident.metadata["escalated"] = "true"
        incident.metadata["escalated_to"] = "sre-oncall"
    return {"status": "ok", "message": f"Incident {incident_id} escalated to SRE on-call"}
