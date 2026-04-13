"""Fire-and-forget outbound notifications for incident lifecycle events."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

import httpx

if TYPE_CHECKING:
    from .models import Incident, WebhookIntegrationsConfig

logger = logging.getLogger(__name__)


def _slack_payload(text: str) -> Dict[str, Any]:
    return {"text": text, "username": "Nexovo Helling Cloud", "icon_emoji": ":cloud:"}


def _generic_payload(incident_id: str, event: str, service: str, severity: str, detail: str) -> Dict[str, Any]:
    return {
        "source": "nexovo-helling-cloud",
        "event": event,
        "incident_id": incident_id,
        "service": service,
        "severity": severity,
        "detail": detail,
    }


def notify_integrations(
    config: Optional["WebhookIntegrationsConfig"],
    incident: "Incident",
    event: str,
    detail: str,
) -> None:
    if not config:
        return
    service = incident.service
    severity = incident.severity.value if hasattr(incident.severity, "value") else str(incident.severity)
    incident_id = incident.id
    text = f"*{event.upper()}*\n• Service: `{service}`\n• Severity: `{severity}`\n• Incident: `{incident_id}`\n• {detail}"

    if event == "acknowledged" and not config.notify_on_ack:
        return
    if event == "escalated" and not config.notify_on_escalate:
        return

    with httpx.Client(timeout=8.0) as client:
        if config.slack_webhook_url:
            try:
                r = client.post(config.slack_webhook_url, json=_slack_payload(text))
                r.raise_for_status()
            except Exception as exc:
                logger.warning("Slack webhook failed: %s", exc)

        if config.jira_webhook_url:
            try:
                r = client.post(
                    config.jira_webhook_url,
                    json=_generic_payload(incident_id, event, service, severity, detail),
                )
                r.raise_for_status()
            except Exception as exc:
                logger.warning("Jira webhook failed: %s", exc)

        if config.email_webhook_url:
            try:
                r = client.post(
                    config.email_webhook_url,
                    json=_generic_payload(incident_id, event, service, severity, detail),
                )
                r.raise_for_status()
            except Exception as exc:
                logger.warning("Email webhook failed: %s", exc)
