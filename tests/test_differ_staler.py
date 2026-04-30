"""Tests for driftwatch.differ_staler."""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.differ_staler import (
    StaleEntry,
    StalenessReport,
    _days_since,
    _first_seen_for,
    detect_stale,
)


def _entry(
    resource_id: str = "res-1",
    kind: str = "instance",
    provider: str = "aws",
    change_type: str = "changed",
) -> DriftEntry:
    return DriftEntry(
        resource_id=resource_id,
        kind=kind,
        provider=provider,
        change_type=change_type,
        attribute_diff={},
    )


def _report(*entries: DriftEntry) -> DriftReport:
    r = DriftReport()
    for e in entries:
        r.entries.append(e)
    return r


def _iso(days_ago: float = 0.0) -> str:
    dt = datetime.now(tz=timezone.utc) - timedelta(days=days_ago)
    return dt.isoformat()


def _make_history(resource_id: str, kind: str, provider: str, days_ago: float):
    return [
        {
            "timestamp": _iso(days_ago),
            "entries": [
                {"resource_id": resource_id, "kind": kind, "provider": provider}
            ],
        }
    ]


def test_detect_stale_empty_report():
    result = detect_stale(_report(), threshold_days=7.0)
    assert result.entries == []
    assert result.to_dict()["total"] == 0
    assert result.to_dict()["stale_count"] == 0


def test_detect_stale_no_history_not_stale():
    with patch("driftwatch.differ_staler.load_history", return_value=[]):
        result = detect_stale(_report(_entry()), threshold_days=3.0)
    assert len(result.entries) == 1
    se = result.entries[0]
    assert se.is_stale is False
    assert se.first_seen == ""
    assert se.days_stale == 0.0


def test_detect_stale_recent_entry_not_stale():
    history = _make_history("res-1", "instance", "aws", days_ago=1.0)
    with patch("driftwatch.differ_staler.load_history", return_value=history):
        result = detect_stale(_report(_entry()), threshold_days=7.0)
    assert result.entries[0].is_stale is False
    assert result.entries[0].days_stale < 7.0


def test_detect_stale_old_entry_is_stale():
    history = _make_history("res-1", "instance", "aws", days_ago=10.0)
    with patch("driftwatch.differ_staler.load_history", return_value=history):
        result = detect_stale(_report(_entry()), threshold_days=7.0)
    se = result.entries[0]
    assert se.is_stale is True
    assert se.days_stale >= 7.0


def test_detect_stale_mixed_entries():
    e1 = _entry(resource_id="old", kind="instance", provider="aws")
    e2 = _entry(resource_id="new", kind="bucket", provider="gcp")
    history = [
        {
            "timestamp": _iso(15.0),
            "entries": [{"resource_id": "old", "kind": "instance", "provider": "aws"}],
        },
        {
            "timestamp": _iso(0.5),
            "entries": [{"resource_id": "new", "kind": "bucket", "provider": "gcp"}],
        },
    ]
    with patch("driftwatch.differ_staler.load_history", return_value=history):
        result = detect_stale(_report(e1, e2), threshold_days=7.0)
    stale_ids = {se.entry.resource_id for se in result.entries if se.is_stale}
    fresh_ids = {se.entry.resource_id for se in result.entries if not se.is_stale}
    assert "old" in stale_ids
    assert "new" in fresh_ids
    assert result.to_dict()["stale_count"] == 1


def test_to_dict_structure():
    history = _make_history("res-1", "instance", "aws", days_ago=8.0)
    with patch("driftwatch.differ_staler.load_history", return_value=history):
        result = detect_stale(_report(_entry()), threshold_days=7.0)
    d = result.to_dict()
    assert "threshold_days" in d
    assert "total" in d
    assert "stale_count" in d
    assert "entries" in d
    row = d["entries"][0]
    assert "resource_id" in row
    assert "days_stale" in row
    assert "is_stale" in row
    assert "first_seen" in row


def test_days_since_far_past():
    ts = _iso(30.0)
    assert _days_since(ts) >= 29.9


def test_days_since_bad_value():
    assert _days_since("not-a-date") == 0.0
