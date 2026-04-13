from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class RemediationAction(str, Enum):
    restart_pod = "restart_pod"
    rollback_deployment = "rollback_deployment"
    scale_deployment = "scale_deployment"
    config_patch = "config_patch"
    notify_human = "notify_human"


class SignalWindow(BaseModel):
    service: str
    namespace: str = "default"
    cpu: float = Field(ge=0, le=100)
    memory: float = Field(ge=0, le=100)
    error_rate: float = Field(ge=0, le=100)
    p95_latency_ms: float = Field(gt=0)
    log_error_count: int = Field(ge=0)
    deploy_changed_last_15m: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Incident(BaseModel):
    id: str
    service: str
    severity: Severity
    anomaly_score: float
    confidence: float
    hypothesis: str
    recommended_action: RemediationAction
    created_at: datetime = Field(default_factory=datetime.utcnow)
    executed: bool = False
    metadata: Dict[str, str] = Field(default_factory=dict)


class ActionResult(BaseModel):
    incident_id: str
    action: RemediationAction
    success: bool
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DetectionResponse(BaseModel):
    incident: Optional[Incident]
    action_result: Optional[ActionResult]
    reasons: List[str]


class IncidentAssignmentRequest(BaseModel):
    owner: str
    actor: str = "dashboard-user"


class AuditEvent(BaseModel):
    id: str
    incident_id: str
    event_type: str
    actor: str
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class IncidentComment(BaseModel):
    id: str
    incident_id: str
    author: str
    body: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CreateCommentRequest(BaseModel):
    author: str = "operator"
    body: str


class WebhookIntegrationsConfig(BaseModel):
    slack_webhook_url: str = ""
    jira_webhook_url: str = ""
    email_webhook_url: str = ""
    notify_on_ack: bool = True
    notify_on_escalate: bool = True
