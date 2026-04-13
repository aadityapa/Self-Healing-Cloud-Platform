from __future__ import annotations

from dataclasses import dataclass, field
import math
import random
from threading import Lock
from typing import Dict, List, Tuple
from uuid import uuid4

from .models import (
    ActionResult,
    AuditEvent,
    DetectionResponse,
    Incident,
    RemediationAction,
    Severity,
    SignalWindow,
)


@dataclass
class StateStore:
    incidents: List[Incident] = field(default_factory=list)
    actions: List[ActionResult] = field(default_factory=list)
    audit_events: List[AuditEvent] = field(default_factory=list)
    lock: Lock = field(default_factory=Lock)


class DetectionEngine:
    def __init__(self) -> None:
        self.mean_vector, self.std_vector = self._fit_bootstrap_baseline()

    def _fit_bootstrap_baseline(self) -> Tuple[List[float], List[float]]:
        rng = random.Random(42)
        rows: List[List[float]] = []
        for _ in range(1800):
            rows.append(
                [
                    rng.gauss(45, 8),  # cpu
                    rng.gauss(55, 10),  # memory
                    max(0.0, rng.gauss(0.8, 0.4)),  # error rate
                    max(10.0, rng.gauss(170, 35)),  # p95 latency
                    max(0.0, rng.gauss(8, 5)),  # log errors
                    float(rng.randint(0, 1)),  # deploy changed
                ]
            )
        cols = list(zip(*rows))
        means = [sum(c) / len(c) for c in cols]
        stds: List[float] = []
        for idx, c in enumerate(cols):
            variance = sum((v - means[idx]) ** 2 for v in c) / len(c)
            stds.append(math.sqrt(variance) + 1e-6)
        return means, stds

    def predict(self, signal: SignalWindow) -> Tuple[float, bool]:
        vector = [
            signal.cpu,
            signal.memory,
            signal.error_rate,
            signal.p95_latency_ms,
            float(signal.log_error_count),
            1.0 if signal.deploy_changed_last_15m else 0.0,
        ]
        z_scores = [
            abs((value - self.mean_vector[i]) / self.std_vector[i])
            for i, value in enumerate(vector)
        ]
        score = sum(z_scores) / len(z_scores)
        is_anomaly = score > 2.8
        return score, is_anomaly


class PolicyEngine:
    def decide(self, signal: SignalWindow, anomaly_score: float) -> DetectionResponse:
        reasons: List[str] = []
        confidence = min(0.99, max(0.1, anomaly_score / 0.35))
        severity = Severity.low

        if signal.error_rate > 7 or signal.p95_latency_ms > 850:
            severity = Severity.critical
            reasons.append("Critical SLI breach (error/latency)")
        elif signal.error_rate > 3 or signal.cpu > 90 or signal.memory > 92:
            severity = Severity.high
            reasons.append("High utilization or elevated errors")
        elif signal.error_rate > 1.5 or signal.p95_latency_ms > 450:
            severity = Severity.medium
            reasons.append("Degraded behavior above baseline")

        action = RemediationAction.notify_human
        hypothesis = "Transient instability"

        if signal.deploy_changed_last_15m and signal.error_rate > 3:
            action = RemediationAction.rollback_deployment
            hypothesis = "Recent rollout likely introduced regression"
            reasons.append("Deployment event correlates with errors")
        elif signal.cpu > 92 and signal.error_rate < 3:
            action = RemediationAction.scale_deployment
            hypothesis = "Capacity bottleneck under load"
            reasons.append("CPU saturation suggests scale-out")
        elif signal.log_error_count > 80 and signal.memory > 90:
            action = RemediationAction.restart_pod
            hypothesis = "Possible memory leak or deadlocked workers"
            reasons.append("Error bursts and high memory footprint")
        elif signal.error_rate > 5:
            action = RemediationAction.config_patch
            hypothesis = "Known bad config pattern or timeout mismatch"
            reasons.append("Error threshold crossed for safe config mitigation")

        incident = Incident(
            id=str(uuid4()),
            service=signal.service,
            severity=severity,
            anomaly_score=anomaly_score,
            confidence=confidence,
            hypothesis=hypothesis,
            recommended_action=action,
            metadata={
                "namespace": signal.namespace,
                "cpu": f"{signal.cpu:.2f}",
                "memory": f"{signal.memory:.2f}",
                "error_rate": f"{signal.error_rate:.2f}",
                "latency_ms": f"{signal.p95_latency_ms:.2f}",
            },
        )
        return DetectionResponse(incident=incident, action_result=None, reasons=reasons)


class RemediationEngine:
    def execute(self, incident: Incident) -> ActionResult:
        high_risk = incident.recommended_action in {
            RemediationAction.rollback_deployment,
            RemediationAction.config_patch,
        }

        if high_risk and incident.confidence < 0.65:
            return ActionResult(
                incident_id=incident.id,
                action=RemediationAction.notify_human,
                success=False,
                message="Blocked by safety policy: confidence too low for high-risk action",
            )

        action_message: Dict[RemediationAction, str] = {
            RemediationAction.restart_pod: "Restarted unhealthy pods for service",
            RemediationAction.rollback_deployment: "Triggered Argo rollout undo",
            RemediationAction.scale_deployment: "Scaled deployment replicas +2",
            RemediationAction.config_patch: "Applied safe config patch template",
            RemediationAction.notify_human: "Sent Slack notification for manual intervention",
        }
        return ActionResult(
            incident_id=incident.id,
            action=incident.recommended_action,
            success=True,
            message=action_message[incident.recommended_action],
        )
