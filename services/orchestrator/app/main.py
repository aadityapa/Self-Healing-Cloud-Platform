from datetime import datetime
from typing import Dict, List
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest
from starlette.responses import Response

from .engine import DetectionEngine, PolicyEngine, RemediationEngine, StateStore
from .models import (
    ActionResult,
    AuditEvent,
    CreateCommentRequest,
    DetectionResponse,
    Incident,
    IncidentAssignmentRequest,
    IncidentComment,
    SignalWindow,
    WebhookIntegrationsConfig,
)
from .webhooks_notifier import notify_integrations

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
        state.audit_events.insert(
            0,
            AuditEvent(
                id=str(uuid4()),
                incident_id=incident.id,
                event_type="remediation_executed",
                actor="system",
                message=f"Executed action {result.action.value} with success={result.success}",
                created_at=datetime.utcnow(),
            ),
        )

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


@app.get("/v1/audit", response_model=List[AuditEvent])
def list_audit_events() -> List[AuditEvent]:
    return state.audit_events[:300]


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
        state.audit_events.insert(
            0,
            AuditEvent(
                id=str(uuid4()),
                incident_id=incident.id,
                event_type="acknowledged",
                actor="dashboard-user",
                message=f"Incident {incident.id} acknowledged",
                created_at=datetime.utcnow(),
            ),
        )
        cfg = state.webhook_config.model_copy()
    notify_integrations(cfg, incident, "acknowledged", "Incident acknowledged via dashboard")
    return {"status": "ok", "message": f"Incident {incident_id} acknowledged"}


@app.post("/v1/incidents/{incident_id}/escalate")
def escalate_incident(incident_id: str) -> Dict[str, str]:
    with state.lock:
        incident = _get_incident_or_404(incident_id)
        incident.metadata["escalated"] = "true"
        incident.metadata["escalated_to"] = "sre-oncall"
        state.audit_events.insert(
            0,
            AuditEvent(
                id=str(uuid4()),
                incident_id=incident.id,
                event_type="escalated",
                actor="dashboard-user",
                message=f"Incident {incident.id} escalated to sre-oncall",
                created_at=datetime.utcnow(),
            ),
        )
        cfg = state.webhook_config.model_copy()
    notify_integrations(cfg, incident, "escalated", "Incident escalated to SRE on-call")
    return {"status": "ok", "message": f"Incident {incident_id} escalated to SRE on-call"}


@app.post("/v1/incidents/{incident_id}/assign")
def assign_incident_owner(
    incident_id: str, request: IncidentAssignmentRequest
) -> Dict[str, str]:
    with state.lock:
        incident = _get_incident_or_404(incident_id)
        incident.metadata["owner"] = request.owner
        incident.metadata["acknowledged"] = incident.metadata.get("acknowledged", "false")
        state.audit_events.insert(
            0,
            AuditEvent(
                id=str(uuid4()),
                incident_id=incident.id,
                event_type="owner_assigned",
                actor=request.actor,
                message=f"Assigned owner `{request.owner}`",
                created_at=datetime.utcnow(),
            ),
        )
    return {"status": "ok", "message": f"Incident {incident_id} assigned to {request.owner}"}


@app.get("/v1/integrations/webhooks", response_model=WebhookIntegrationsConfig)
def get_webhook_integrations() -> WebhookIntegrationsConfig:
    return state.webhook_config


@app.put("/v1/integrations/webhooks", response_model=WebhookIntegrationsConfig)
def put_webhook_integrations(body: WebhookIntegrationsConfig) -> WebhookIntegrationsConfig:
    with state.lock:
        state.webhook_config = body
    return state.webhook_config


@app.get("/v1/incidents/{incident_id}/comments", response_model=List[IncidentComment])
def list_incident_comments(incident_id: str) -> List[IncidentComment]:
    _get_incident_or_404(incident_id)
    return list(state.comments_by_incident.get(incident_id, []))


@app.post("/v1/incidents/{incident_id}/comments", response_model=IncidentComment)
def add_incident_comment(incident_id: str, body: CreateCommentRequest) -> IncidentComment:
    with state.lock:
        _get_incident_or_404(incident_id)
        comment = IncidentComment(
            id=str(uuid4()),
            incident_id=incident_id,
            author=body.author,
            body=body.body,
            created_at=datetime.utcnow(),
        )
        if incident_id not in state.comments_by_incident:
            state.comments_by_incident[incident_id] = []
        state.comments_by_incident[incident_id].append(comment)
        state.audit_events.insert(
            0,
            AuditEvent(
                id=str(uuid4()),
                incident_id=incident_id,
                event_type="comment_added",
                actor=body.author,
                message=body.body[:200],
                created_at=datetime.utcnow(),
            ),
        )
    return comment
