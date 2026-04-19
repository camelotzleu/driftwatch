"""Tests for differ_deduplicator."""
import pytest
from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.differ_deduplicator import deduplicate_reports, DeduplicatedReport


def _entry(provider="aws", resource_id="i-1", kind="instance", change_type="changed"):
    return DriftEntry(
        provider=provider,
        resource_id=resource_id,
        kind=kind,
        change_type=change_type,
        attribute_diff={},
    )


def _report(*entries):
    return DriftReport(entries=list(entries))


def test_deduplicate_empty_reports():
    result = deduplicate_reports([])
    assert isinstance(result, DeduplicatedReport)
    assert result.entries == []
    assert result.duplicate_count == 0


def test_deduplicate_single_report_no_duplicates():
    e1 = _entry(resource_id="i-1")
    e2 = _entry(resource_id="i-2")
    result = deduplicate_reports([_report(e1, e2)])
    assert len(result.entries) == 2
    assert result.duplicate_count == 0


def test_deduplicate_removes_same_entry_across_reports():
    e1 = _entry(resource_id="i-1")
    e2 = _entry(resource_id="i-1")  # duplicate
    result = deduplicate_reports([_report(e1), _report(e2)])
    assert len(result.entries) == 1
    assert result.duplicate_count == 1


def test_deduplicate_keeps_different_providers():
    e1 = _entry(provider="aws", resource_id="i-1")
    e2 = _entry(provider="gcp", resource_id="i-1")
    result = deduplicate_reports([_report(e1, e2)])
    assert len(result.entries) == 2
    assert result.duplicate_count == 0


def test_deduplicate_multiple_reports_mixed():
    e1 = _entry(resource_id="i-1")
    e2 = _entry(resource_id="i-2")
    e3 = _entry(resource_id="i-1")  # dup of e1
    e4 = _entry(resource_id="i-3")
    result = deduplicate_reports([_report(e1, e2), _report(e3, e4)])
    assert len(result.entries) == 3
    assert result.duplicate_count == 1


def test_to_dict_structure():
    e = _entry()
    result = deduplicate_reports([_report(e)])
    d = result.to_dict()
    assert "entries" in d
    assert "total" in d
    assert "duplicates_removed" in d
    assert d["total"] == 1
    assert d["duplicates_removed"] == 0


def test_first_occurrence_is_kept():
    e1 = _entry(resource_id="i-1", change_type="added")
    e2 = _entry(resource_id="i-1", change_type="changed")
    result = deduplicate_reports([_report(e1), _report(e2)])
    assert result.entries[0].change_type == "added"
