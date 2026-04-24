"""Tests for driftwatch.differ_watchlist."""
from __future__ import annotations

import pytest

from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.differ_watchlist import (
    WatchlistEntry,
    check_watchlist,
    watchlist_from_dicts,
)


def _entry(resource_id: str, change_type: str = "changed") -> DriftEntry:
    return DriftEntry(
        resource_id=resource_id,
        kind="Instance",
        provider="aws",
        change_type=change_type,
        attribute_diff={},
    )


def _report(*entries: DriftEntry) -> DriftReport:
    r = DriftReport()
    for e in entries:
        r.entries.append(e)
    return r


# ---------------------------------------------------------------------------


def test_check_watchlist_empty_report():
    wl = [WatchlistEntry(resource_id="i-123")]
    result = check_watchlist(_report(), wl)
    assert result.total_checked == 0
    assert result.watched == []


def test_check_watchlist_no_hits():
    wl = [WatchlistEntry(resource_id="i-999")]
    result = check_watchlist(_report(_entry("i-123")), wl)
    assert result.total_checked == 1
    assert len(result.watched) == 0


def test_check_watchlist_single_hit():
    wl = [WatchlistEntry(resource_id="i-123", reason="critical")]
    result = check_watchlist(_report(_entry("i-123")), wl)
    assert len(result.watched) == 1
    assert result.watched[0].entry.resource_id == "i-123"
    assert result.watched[0].reason == "critical"


def test_check_watchlist_multiple_hits():
    wl = [
        WatchlistEntry(resource_id="i-1"),
        WatchlistEntry(resource_id="i-2"),
    ]
    result = check_watchlist(_report(_entry("i-1"), _entry("i-2"), _entry("i-3")), wl)
    assert len(result.watched) == 2
    ids = {w.entry.resource_id for w in result.watched}
    assert ids == {"i-1", "i-2"}


def test_check_watchlist_no_reason_is_none():
    wl = [WatchlistEntry(resource_id="i-1")]
    result = check_watchlist(_report(_entry("i-1")), wl)
    assert result.watched[0].reason is None


def test_to_dict_structure():
    wl = [WatchlistEntry(resource_id="i-1", reason="prod")]
    result = check_watchlist(_report(_entry("i-1", "added")), wl)
    d = result.to_dict()
    assert d["total_checked"] == 1
    assert d["watched_hits"] == 1
    assert d["entries"][0]["resource_id"] == "i-1"
    assert d["entries"][0]["change_type"] == "added"
    assert d["entries"][0]["reason"] == "prod"


def test_watchlist_from_dicts_basic():
    raw = [{"resource_id": "i-10", "reason": "sensitive"}, {"resource_id": "i-20"}]
    wl = watchlist_from_dicts(raw)
    assert len(wl) == 2
    assert wl[0].resource_id == "i-10"
    assert wl[0].reason == "sensitive"
    assert wl[1].reason is None


def test_watchlist_from_dicts_skips_missing_id():
    raw = [{"reason": "no id here"}, {"resource_id": "i-5"}]
    wl = watchlist_from_dicts(raw)
    assert len(wl) == 1
    assert wl[0].resource_id == "i-5"
