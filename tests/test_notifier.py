"""Tests for driftwatch.notifier."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.notifier import NotifierConfig, _build_slack_payload, notify, send_webhook


def _make_report(drift: bool = True) -> DriftReport:
    entries = []
    if drift:
        entries.append(
            DriftEntry(
                resource_id="i-123",
                resource_type="ec2",
                change_type="changed",
                diff={"instance_type": ("t2.micro", "t3.micro")},
            )
        )
    return DriftReport(entries=entries)


def test_build_slack_payload_contains_alert():
    report = _make_report()
    payload = _build_slack_payload(report)
    assert "DriftWatch Alert" in payload["text"]
    assert "text" in payload


def test_build_slack_payload_no_drift():
    report = _make_report(drift=False)
    payload = _build_slack_payload(report)
    assert isinstance(payload["text"], str)


def test_send_webhook_returns_true_on_success():
    mock_response = MagicMock()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_response):
        result = send_webhook(_make_report(), "https://hooks.example.com/test")
    assert result is True


def test_send_webhook_returns_false_on_error():
    with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
        result = send_webhook(_make_report(), "https://hooks.example.com/test")
    assert result is False


def test_notify_skips_when_no_drift():
    report = _make_report(drift=False)
    cfg = NotifierConfig(webhook_url="https://hooks.example.com/x")
    with patch("driftwatch.notifier.send_webhook") as mock_send:
        notify(report, cfg)
        mock_send.assert_not_called()


def test_notify_sends_when_drift_and_webhook():
    report = _make_report(drift=True)
    cfg = NotifierConfig(webhook_url="https://hooks.example.com/x")
    with patch("driftwatch.notifier.send_webhook", return_value=True) as mock_send:
        notify(report, cfg)
        mock_send.assert_called_once()


def test_notify_no_webhook_no_send():
    report = _make_report(drift=True)
    cfg = NotifierConfig(webhook_url=None)
    with patch("driftwatch.notifier.send_webhook") as mock_send:
        notify(report, cfg)
        mock_send.assert_not_called()
