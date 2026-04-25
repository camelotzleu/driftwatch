"""Tests for driftwatch/differ_escalator.py"""
from __future__ import annotations

import pytest
from unittest.mock import patch

from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.differ_escalator import (
    EscalatedEntry,
    EscalationReport,
    _count_consecutive,
    escalate_report,
)


def _entry(resource_id="r-1", kind="instance", provider="aws", change_type="changed"):
    return DriftEntry(
        resource_id=resource_id,
        kind=kind,
        provider=provider,
        change_type=change_type,
        attribute_diff={},
    )


def _report(*entries):
    r = DriftReport()
    for e in entries:
        r.entries.append(e)
    return r


def _history_run(*resource_ids, kind="instance"):
    return {"entries": [{"resource_id": rid, "kind": kind} for rid in resource_ids]}


# ---------------------------------------------------------------------------
# _count_consecutive
# ---------------------------------------------------------------------------

def test_count_consecutive_empty_history():
    assert _count_consecutive("r-1", "instance", []) == 0


def test_count_consecutive_single_match():
    history = [_history_run("r-1")]
    assert _count_consecutive("r-1", "instance", history) == 1


def test_count_consecutive_stops_on_gap():
    history = [
        _history_run("r-1"),
        _history_run(),          # gap — r-1 absent
        _history_run("r-1"),
        _history_run("r-1"),
    ]
    # reversed: last two runs have r-1, then gap stops count at 2
    assert _count_consecutive("r-1", "instance", history) == 2


def test_count_consecutive_all_match():
    history = [_history_run("r-1"), _history_run("r-1"), _history_run("r-1")]
    assert _count_consecutive("r-1", "instance", history) == 3


# ---------------------------------------------------------------------------
# escalate_report
# ---------------------------------------------------------------------------

def _empty_history():
    return []


def test_escalate_empty_report():
    with patch("driftwatch.differ_escalator.load_history", return_value=[]):
        result = escalate_report(_report())
    assert isinstance(result, EscalationReport)
    assert result.entries == []
    assert result.to_dict()["escalated_count"] == 0


def test_escalate_changed_below_threshold_not_escalated():
    with patch("driftwatch.differ_escalator.load_history", return_value=[]):
        result = escalate_report(_report(_entry(change_type="changed")), threshold=3)
    assert result.entries[0].escalated is False
    assert result.entries[0].consecutive_runs == 0


def test_escalate_added_always_escalated():
    with patch("driftwatch.differ_escalator.load_history", return_value=[]):
        result = escalate_report(_report(_entry(change_type="added")), threshold=3)
    assert result.entries[0].escalated is True
    assert "High-impact" in result.entries[0].escalation_reason


def test_escalate_removed_always_escalated():
    with patch("driftwatch.differ_escalator.load_history", return_value=[]):
        result = escalate_report(_report(_entry(change_type="removed")), threshold=3)
    assert result.entries[0].escalated is True


def test_escalate_changed_meets_threshold():
    history = [_history_run("r-1"), _history_run("r-1"), _history_run("r-1")]
    with patch("driftwatch.differ_escalator.load_history", return_value=history):
        result = escalate_report(_report(_entry(change_type="changed")), threshold=3)
    e = result.entries[0]
    assert e.escalated is True
    assert e.consecutive_runs == 3
    assert "3" in e.escalation_reason


def test_to_dict_structure():
    with patch("driftwatch.differ_escalator.load_history", return_value=[]):
        result = escalate_report(_report(_entry(change_type="added")))
    d = result.to_dict()
    assert "threshold" in d
    assert "total" in d
    assert "escalated_count" in d
    assert "entries" in d
    assert d["entries"][0]["resource_id"] == "r-1"
