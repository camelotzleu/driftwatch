"""Tests for driftwatch.commands.audit_cmd."""
from __future__ import annotations

import argparse
from unittest.mock import patch, MagicMock

import pytest

from driftwatch.commands.audit_cmd import cmd_audit_show, cmd_audit_clear
from driftwatch.auditor import AuditEntry


def _args(**kwargs):
    defaults = {"config_dir": ".driftwatch", "format": "text"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _entry(provider="aws", has_drift=True):
    return AuditEntry(
        timestamp="2024-01-01T00:00:00+00:00",
        provider=provider,
        total_resources=3,
        added=1,
        removed=1,
        changed=1,
        has_drift=has_drift,
        triggered_alerts=[],
        note=None,
    )


def test_cmd_audit_show_no_entries(capsys):
    with patch("driftwatch.commands.audit_cmd.auditor.load", return_value=[]):
        rc = cmd_audit_show(_args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "No audit entries" in out


def test_cmd_audit_show_text(capsys):
    entries = [_entry("aws", True), _entry("gcp", False)]
    with patch("driftwatch.commands.audit_cmd.auditor.load", return_value=entries):
        rc = cmd_audit_show(_args(format="text"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "aws" in out
    assert "gcp" in out
    assert "YES" in out


def test_cmd_audit_show_json(capsys):
    entries = [_entry("azure", False)]
    with patch("driftwatch.commands.audit_cmd.auditor.load", return_value=entries):
        rc = cmd_audit_show(_args(format="json"))
    assert rc == 0
    import json
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert data[0]["provider"] == "azure"


def test_cmd_audit_clear(capsys):
    with patch("driftwatch.commands.audit_cmd.auditor.clear") as mock_clear:
        rc = cmd_audit_clear(_args())
    assert rc == 0
    mock_clear.assert_called_once_with(config_dir=".driftwatch")
    assert "cleared" in capsys.readouterr().out
