"""Tests for driftwatch.differ_annotator."""
import pytest
from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.differ_annotator import AnnotationRule, AnnotatedEntry, annotate_report


def _entry(resource_id="r-1", kind="instance", provider="aws", change_type="changed"):
    return DriftEntry(
        resource_id=resource_id,
        kind=kind,
        provider=provider,
        change_type=change_type,
        attribute_diff={"state": {"baseline": "running", "current": "stopped"}},
    )


def _report(*entries):
    return DriftReport(entries=list(entries))


def test_annotate_empty_report():
    rules = [AnnotationRule(note="check this", kind="instance")]
    result = annotate_report(_report(), rules)
    assert result.entries == []


def test_annotate_no_rules():
    report = _report(_entry())
    result = annotate_report(report, [])
    assert len(result.entries) == 1
    assert result.entries[0].notes == []


def test_annotate_matching_kind():
    rules = [AnnotationRule(note="instance note", kind="instance")]
    report = _report(_entry(kind="instance"))
    result = annotate_report(report, rules)
    assert "instance note" in result.entries[0].notes


def test_annotate_non_matching_kind():
    rules = [AnnotationRule(note="bucket note", kind="bucket")]
    report = _report(_entry(kind="instance"))
    result = annotate_report(report, rules)
    assert result.entries[0].notes == []


def test_annotate_matching_provider():
    rules = [AnnotationRule(note="aws note", provider="aws")]
    report = _report(_entry(provider="aws"))
    result = annotate_report(report, rules)
    assert "aws note" in result.entries[0].notes


def test_annotate_matching_change_type():
    rules = [AnnotationRule(note="added note", change_type="added")]
    report = _report(_entry(change_type="added"), _entry(change_type="removed"))
    result = annotate_report(report, rules)
    assert "added note" in result.entries[0].notes
    assert result.entries[1].notes == []


def test_annotate_multiple_rules_applied():
    rules = [
        AnnotationRule(note="is aws", provider="aws"),
        AnnotationRule(note="is instance", kind="instance"),
    ]
    report = _report(_entry(kind="instance", provider="aws"))
    result = annotate_report(report, rules)
    assert "is aws" in result.entries[0].notes
    assert "is instance" in result.entries[0].notes


def test_to_dict_structure():
    entry = _entry()
    ae = AnnotatedEntry(entry=entry, notes=["test note"])
    d = ae.to_dict()
    assert d["resource_id"] == "r-1"
    assert d["notes"] == ["test note"]
    assert "attribute_diff" in d


def test_annotation_report_to_dict():
    report = _report(_entry())
    rules = [AnnotationRule(note="n", kind="instance")]
    result = annotate_report(report, rules)
    d = result.to_dict()
    assert "annotated_entries" in d
    assert len(d["annotated_entries"]) == 1
