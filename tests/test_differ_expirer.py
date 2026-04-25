"""Tests for driftwatch.differ_expirer."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import pytest

from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.differ_expirer import (
    check_expiry,
    _first_seen_for,
    _age_days,
    ExpiredEntry,
    ExpiryReport,
)


def _entry(resource_id="res-1", kind="instance", provider="aws", change_type="changed"):
    return DriftEntry(
        resource_id=resource_id,
        kind=kind,
        provider=provider,
        change_type=change_type,
        attribute_diffs={},
    )


def _report(*entries):
    r = DriftReport()
    for e in entries:
        r.entries.append(e)
    return r


def _history_run(resource_id: str, ts: str):
    return {
        "timestamp": ts,
        "report": {"entries": [{"resource_id": resource_id}]},
    }


# ---------------------------------------------------------------------------
# _first_seen_for
# ---------------------------------------------------------------------------

def test_first_seen_returns_none_when_empty():
    assert _first_seen_for("res-1", []) is None


def test_first_seen_returns_earliest_match():
    history = [
        _history_run("res-1", "2024-01-01T00:00:00+00:00"),
        _history_run("res-1", "2024-01-05T00:00:00+00:00"),
    ]
    assert _first_seen_for("res-1", history) == "2024-01-01T00:00:00+00:00"


def test_first_seen_ignores_other_resources():
    history = [_history_run("res-99", "2024-01-01T00:00:00+00:00")]
    assert _first_seen_for("res-1", history) is None


# ---------------------------------------------------------------------------
# _age_days
# ---------------------------------------------------------------------------

def test_age_days_recent():
    now = datetime.now(timezone.utc)
    two_days_ago = (now - timedelta(days=2)).isoformat()
    age = _age_days(two_days_ago)
    assert 1.9 < age < 2.1


# ---------------------------------------------------------------------------
# check_expiry
# ---------------------------------------------------------------------------

def test_check_expiry_empty_report():
    result = check_expiry(_report(), ttl_days=7)
    assert result.to_dict()["total"] == 0
    assert result.to_dict()["expired_count"] == 0


def test_check_expiry_no_history_not_expired():
    with patch("driftwatch.differ_expirer.load_history", return_value=[]):
        result = check_expiry(_report(_entry()), ttl_days=7)
    assert result.to_dict()["expired_count"] == 0
    assert result.entries[0].expired is False


def test_check_expiry_old_entry_is_expired():
    old_ts = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    history = [_history_run("res-1", old_ts)]
    with patch("driftwatch.differ_expirer.load_history", return_value=history):
        result = check_expiry(_report(_entry("res-1")), ttl_days=7)
    assert result.entries[0].expired is True
    assert result.to_dict()["expired_count"] == 1


def test_check_expiry_recent_entry_not_expired():
    recent_ts = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    history = [_history_run("res-1", recent_ts)]
    with patch("driftwatch.differ_expirer.load_history", return_value=history):
        result = check_expiry(_report(_entry("res-1")), ttl_days=7)
    assert result.entries[0].expired is False


def test_to_dict_structure():
    report = ExpiryReport()
    d = report.to_dict()
    assert "total" in d
    assert "expired_count" in d
    assert "entries" in d
