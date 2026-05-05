"""Tests for driftwatch.commands.aggregate_cmd."""
from __future__ import annotations

import argparse
import json
from unittest.mock import patch

import pytest

from driftwatch.commands.aggregate_cmd import cmd_aggregate


def _args(limit: int = 5, fmt: str = "text") -> argparse.Namespace:
    return argparse.Namespace(limit=limit, format=fmt)


def _history_entry(ts: str, resource_id: str, change_type: str = "changed"):
    return {
        "timestamp": ts,
        "report": {
            "entries": [
                {
                    "resource_id": resource_id,
                    "kind": "instance",
                    "provider": "aws",
                    "change_type": change_type,
                    "attribute_diff": {},
                }
            ]
        },
    }


def test_cmd_aggregate_no_history(capsys):
    with patch("driftwatch.commands.aggregate_cmd.history.load", return_value=[]):
        rc = cmd_aggregate(_args())
    assert rc == 1
    captured = capsys.readouterr()
    assert "No history" in captured.err


def test_cmd_aggregate_text_output(capsys):
    entries = [
        _history_entry("2024-01-01T00:00:00", "res-1"),
        _history_entry("2024-01-02T00:00:00", "res-1"),
    ]
    with patch("driftwatch.commands.aggregate_cmd.history.load", return_value=entries):
        rc = cmd_aggregate(_args(fmt="text"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "res-1" in out
    assert "occurrences=2" in out


def test_cmd_aggregate_json_output(capsys):
    entries = [_history_entry("2024-01-01T00:00:00", "res-42")]
    with patch("driftwatch.commands.aggregate_cmd.history.load", return_value=entries):
        rc = cmd_aggregate(_args(fmt="json"))
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["total_reports"] == 1
    assert data["total_entries"] == 1
    assert data["entries"][0]["resource_id"] == "res-42"


def test_cmd_aggregate_respects_limit(capsys):
    entries = [
        _history_entry(f"2024-01-0{i}T00:00:00", f"res-{i}") for i in range(1, 6)
    ]
    with patch("driftwatch.commands.aggregate_cmd.history.load", return_value=entries):
        rc = cmd_aggregate(_args(limit=2, fmt="json"))
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    # Only last 2 entries => 2 unique resources
    assert data["total_reports"] == 2
