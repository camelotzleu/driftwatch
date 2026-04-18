"""Notification backends for drift alerts."""
from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Optional

from driftwatch.differ import DriftReport
from driftwatch.reporter import render


@dataclass
class NotifierConfig:
    webhook_url: Optional[str] = None
    email: Optional[str] = None  # placeholder for future SMTP support


def _build_slack_payload(report: DriftReport) -> dict:
    text = "\n".join(render(report, fmt="text").splitlines()[:20])
    return {
        "text": f":rotating_light: *DriftWatch Alert* :rotating_light:\n```{text}```"
    }


def send_webhook(report: DriftReport, webhook_url: str, timeout: int = 10) -> bool:
    """POST a Slack-compatible JSON payload to *webhook_url*.

    Returns True on success, False on failure.
    """
    payload = _build_slack_payload(report)
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout):
            return True
    except Exception:  # noqa: BLE001
        return False


def notify(report: DriftReport, cfg: NotifierConfig) -> None:
    """Dispatch notifications based on *cfg*."""
    if not report.has_drift():
        return
    if cfg.webhook_url:
        send_webhook(report, cfg.webhook_url)
