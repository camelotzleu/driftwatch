"""Tests for driftwatch.differ_resolver."""
from __future__ import annotations

import pytest

from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.differ_resolver import (
    ResolutionReport,
    ResolvedEntry,
    resolve_report,
)


def _entry(resource_id: str, change_type: str = "changed") -> DriftEntry:
    return DriftEntry(
        resource_id=resource_id,
        kind="Instance",
        provider="aws",
        change_type=change_type,
        attribute_diff={"state": ("running", "stopped")},
    )


def _report(*resource_ids: str) -> DriftReport:
    report = DriftReport()
    for rid in resource_ids:
        report.entries.append(_entry(rid))
    return report


def test_resolve_empty_report():
    report = _report()
    result = resolve_report(report, resource_ids=["i-123"])
    assert result.resolved == []
    assert result.unresolved == []


def test_resolve_matching_entry():
    report = _report("i-aaa", "i-bbb")
    result = resolve_report(
        report,
        resource_ids=["i-aaa"],
        resolved_by="alice",
        note="handled manually",
        resolved_at="2024-01-01T00:00:00+00:00",
    )
    assert len(result.resolved) == 1
    assert len(result.unresolved) == 1
    r = result.resolved[0]
    assert r.entry.resource_id == "i-aaa"
    assert r.resolved_by == "alice"
    assert r.note == "handled manually"
    assert r.resolved_at == "2024-01-01T00:00:00+00:00"
    assert result.unresolved[0].resource_id == "i-bbb"


def test_resolve_no_matching_entries():
    report = _report("i-aaa", "i-bbb")
    result = resolve_report(report, resource_ids=["i-zzz"])
    assert result.resolved == []
    assert len(result.unresolved) == 2


def test_resolve_all_entries():
    report = _report("i-1", "i-2", "i-3")
    result = resolve_report(report, resource_ids=["i-1", "i-2", "i-3"])
    assert len(result.resolved) == 3
    assert result.unresolved == []


def test_to_dict_structure():
    report = _report("i-x", "i-y")
    result = resolve_report(
        report,
        resource_ids=["i-x"],
        resolved_by="bob",
        resolved_at="2024-06-01T12:00:00+00:00",
    )
    d = result.to_dict()
    assert d["total_resolved"] == 1
    assert d["total_unresolved"] == 1
    assert d["resolved"][0]["resource_id"] == "i-x"
    assert d["resolved"][0]["resolved_by"] == "bob"
    assert d["unresolved"][0]["resource_id"] == "i-y"


def test_resolved_entry_to_dict_keys():
    entry = _entry("i-abc", change_type="added")
    re = ResolvedEntry(
        entry=entry,
        resolved_at="2024-01-01T00:00:00+00:00",
        resolved_by="ci",
        note="auto",
    )
    d = re.to_dict()
    for key in ("resource_id", "kind", "provider", "change_type", "resolved_at", "resolved_by", "note"):
        assert key in d


def test_resolve_uses_default_resolved_by():
    report = _report("i-1")
    result = resolve_report(report, resource_ids=["i-1"])
    assert result.resolved[0].resolved_by == "unknown"
