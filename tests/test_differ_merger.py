"""Tests for driftwatch.differ_merger."""
import pytest
from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.differ_merger import merge_reports, MergeReport


def _entry(resource_id="res-1", kind="instance", provider="aws", change_type="changed", diff=None):
    return DriftEntry(
        resource_id=resource_id,
        kind=kind,
        provider=provider,
        change_type=change_type,
        attribute_diff=diff or {},
    )


def _report(added=None, removed=None, changed=None):
    return DriftReport(
        added=added or [],
        removed=removed or [],
        changed=changed or [],
    )


def test_merge_empty_reports():
    result = merge_reports([])
    assert isinstance(result, MergeReport)
    assert result.total == 0
    assert result.duplicates_removed == 0
    assert result.entries == []


def test_merge_single_report():
    r = _report(added=[_entry("a", change_type="added")], changed=[_entry("b")])
    result = merge_reports([r], sources=["snap1"])
    assert result.total == 2
    assert result.sources == ["snap1"]
    assert result.duplicates_removed == 0


def test_merge_deduplicates_same_entry():
    e = _entry("res-1", change_type="changed")
    r1 = _report(changed=[e])
    r2 = _report(changed=[_entry("res-1", change_type="changed")])
    result = merge_reports([r1, r2])
    assert result.total == 1
    assert result.duplicates_removed == 1


def test_merge_keeps_distinct_entries():
    r1 = _report(added=[_entry("a", change_type="added")])
    r2 = _report(removed=[_entry("b", change_type="removed")])
    result = merge_reports([r1, r2])
    assert result.total == 2
    assert result.duplicates_removed == 0


def test_merge_different_providers_not_deduplicated():
    e1 = _entry("res-1", provider="aws", change_type="changed")
    e2 = _entry("res-1", provider="gcp", change_type="changed")
    result = merge_reports([_report(changed=[e1]), _report(changed=[e2])])
    assert result.total == 2


def test_to_dict_structure():
    r = _report(changed=[_entry()])
    result = merge_reports([r], sources=["s1"])
    d = result.to_dict()
    assert "sources" in d
    assert "total" in d
    assert "duplicates_removed" in d
    assert "entries" in d
    assert d["entries"][0]["resource_id"] == "res-1"


def test_default_source_names():
    result = merge_reports([_report(), _report()])
    assert result.sources == ["report_0", "report_1"]
