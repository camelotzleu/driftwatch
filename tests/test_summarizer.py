"""Tests for driftwatch.summarizer."""
import pytest
from driftwatch.differ import DriftReport, DriftEntry
from driftwatch.summarizer import summarize, format_digest, DriftSummary


def _entry(resource_id: str, change_type: str) -> DriftEntry:
    return DriftEntry(
        resource_id=resource_id,
        change_type=change_type,
        attribute_diff={"key": {"baseline": "a", "current": "b"}} if change_type == "changed" else {},
    )


def _report(*entries: DriftEntry) -> DriftReport:
    return DriftReport(entries=list(entries))


def test_summarize_empty_report():
    s = summarize(_report())
    assert s.total == 0
    assert s.added == 0
    assert s.removed == 0
    assert s.changed == 0
    assert s.providers == []


def test_summarize_counts():
    r = _report(
        _entry("aws:i-001", "added"),
        _entry("aws:i-002", "removed"),
        _entry("aws:i-003", "changed"),
        _entry("gcp:vm-1", "changed"),
    )
    s = summarize(r)
    assert s.total == 4
    assert s.added == 1
    assert s.removed == 1
    assert s.changed == 2


def test_summarize_providers_deduplicated():
    r = _report(
        _entry("aws:i-001", "added"),
        _entry("aws:i-002", "changed"),
        _entry("gcp:vm-1", "removed"),
    )
    s = summarize(r)
    assert "aws" in s.providers
    assert "gcp" in s.providers
    assert len(s.providers) == 2


def test_summarize_top_changes_limited():
    entries = [_entry(f"aws:i-{i:03d}", "changed") for i in range(10)]
    s = summarize(_report(*entries))
    assert len(s.top_changes) == 5


def test_summarize_to_dict_keys():
    s = summarize(_report(_entry("aws:i-001", "added")))
    d = s.to_dict()
    assert set(d.keys()) == {"total", "added", "removed", "changed", "providers", "top_changes"}


def test_format_digest_no_drift():
    s = DriftSummary()
    text = format_digest(s)
    assert "0 resource(s)" in text


def test_format_digest_with_drift():
    r = _report(
        _entry("aws:i-001", "added"),
        _entry("aws:i-002", "changed"),
    )
    s = summarize(r)
    text = format_digest(s)
    assert "Added:   1" in text
    assert "Changed: 1" in text
    assert "aws" in text


def test_format_digest_lists_top_changed():
    r = _report(_entry("azure:vm-99", "changed"))
    s = summarize(r)
    text = format_digest(s)
    assert "azure:vm-99" in text
