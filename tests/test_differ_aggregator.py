"""Tests for driftwatch.differ_aggregator."""
from __future__ import annotations

import pytest

from driftwatch.differ import DriftReport, DriftEntry
from driftwatch.differ_aggregator import (
    AggregatedEntry,
    AggregationReport,
    aggregate_reports,
)


def _entry(
    resource_id: str = "res-1",
    kind: str = "instance",
    provider: str = "aws",
    change_type: str = "changed",
    attribute_diff: dict | None = None,
) -> DriftEntry:
    return DriftEntry(
        resource_id=resource_id,
        kind=kind,
        provider=provider,
        change_type=change_type,
        attribute_diff=attribute_diff or {},
    )


def _report(*entries: DriftEntry) -> DriftReport:
    return DriftReport(entries=list(entries))


def test_aggregate_empty_reports():
    result = aggregate_reports([])
    assert result.total_reports == 0
    assert result.entries == []
    assert result.to_dict()["total_entries"] == 0


def test_aggregate_single_report():
    r = _report(_entry("res-1"), _entry("res-2"))
    result = aggregate_reports([r], labels=["run-1"])
    assert result.total_reports == 1
    assert len(result.entries) == 2


def test_aggregate_deduplicates_across_reports():
    e = _entry("res-1")
    r1 = _report(e)
    r2 = _report(e)
    result = aggregate_reports([r1, r2], labels=["r1", "r2"])
    assert len(result.entries) == 1
    assert result.entries[0].occurrences == 2
    assert result.entries[0].sources == ["r1", "r2"]


def test_aggregate_different_resources_not_merged():
    r1 = _report(_entry("res-1"))
    r2 = _report(_entry("res-2"))
    result = aggregate_reports([r1, r2])
    assert len(result.entries) == 2
    for e in result.entries:
        assert e.occurrences == 1


def test_aggregate_auto_labels():
    r1 = _report(_entry("res-1"))
    r2 = _report(_entry("res-1"))
    result = aggregate_reports([r1, r2])
    assert result.entries[0].sources == ["report_0", "report_1"]


def test_aggregate_sources_not_duplicated_for_same_label():
    e = _entry("res-1")
    r = _report(e, e)
    # Two identical entries in one report — same key, second increments occurrences
    result = aggregate_reports([r], labels=["run-1"])
    assert len(result.entries) == 1
    assert result.entries[0].sources == ["run-1"]
    assert result.entries[0].occurrences == 2


def test_to_dict_structure():
    r = _report(_entry("x", attribute_diff={"cpu": {"old": "2", "new": "4"}}))
    result = aggregate_reports([r], labels=["t0"])
    d = result.to_dict()
    assert "total_reports" in d
    assert "total_entries" in d
    assert "entries" in d
    entry_d = d["entries"][0]
    assert entry_d["resource_id"] == "x"
    assert entry_d["attribute_diff"] == {"cpu": {"old": "2", "new": "4"}}
