"""Tests for driftwatch.labeler."""
import pytest
from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.labeler import (
    LabelRule,
    label_entry,
    label_report,
    label_rules_from_list,
)


def _entry(kind="instance", provider="aws", change_type="changed", attr_diff=None):
    return DriftEntry(
        resource_id="r-1",
        kind=kind,
        provider=provider,
        change_type=change_type,
        attribute_diff=attr_diff or {},
    )


def _report(*entries):
    r = DriftReport()
    for e in entries:
        r.entries.append(e)
    return r


def test_label_entry_no_rules():
    labeled = label_entry(_entry(), [])
    assert labeled.labels == []


def test_label_entry_matching_kind():
    rule = LabelRule(label="compute", kind="instance")
    labeled = label_entry(_entry(kind="instance"), [rule])
    assert "compute" in labeled.labels


def test_label_entry_non_matching_kind():
    rule = LabelRule(label="compute", kind="bucket")
    labeled = label_entry(_entry(kind="instance"), [rule])
    assert labeled.labels == []


def test_label_entry_matching_provider():
    rule = LabelRule(label="aws-resource", provider="aws")
    labeled = label_entry(_entry(provider="aws"), [rule])
    assert "aws-resource" in labeled.labels


def test_label_entry_attribute_contains_match():
    rule = LabelRule(label="tag-drift", attribute_contains="tags")
    e = _entry(attr_diff={"tags.env": {"baseline": "prod", "current": "dev"}})
    labeled = label_entry(e, [rule])
    assert "tag-drift" in labeled.labels


def test_label_entry_attribute_contains_no_match():
    rule = LabelRule(label="tag-drift", attribute_contains="tags")
    e = _entry(attr_diff={"instance_type": {"baseline": "t2.micro", "current": "t3.micro"}})
    labeled = label_entry(e, [rule])
    assert labeled.labels == []


def test_label_entry_multiple_rules():
    rules = [
        LabelRule(label="compute", kind="instance"),
        LabelRule(label="aws-resource", provider="aws"),
    ]
    labeled = label_entry(_entry(kind="instance", provider="aws"), rules)
    assert "compute" in labeled.labels
    assert "aws-resource" in labeled.labels


def test_label_report_returns_all_entries():
    report = _report(_entry(kind="instance"), _entry(kind="bucket"))
    rule = LabelRule(label="compute", kind="instance")
    results = label_report(report, [rule])
    assert len(results) == 2
    assert results[0].labels == ["compute"]
    assert results[1].labels == []


def test_label_rules_from_list():
    raw = [{"label": "critical", "kind": "instance", "attribute_contains": "security"}]
    rules = label_rules_from_list(raw)
    assert len(rules) == 1
    assert rules[0].label == "critical"
    assert rules[0].kind == "instance"
    assert rules[0].attribute_contains == "security"


def test_labeled_entry_to_dict():
    e = _entry(attr_diff={"size": {"baseline": "1", "current": "2"}})
    from driftwatch.labeler import LabeledEntry
    le = LabeledEntry(entry=e, labels=["infra"])
    d = le.to_dict()
    assert d["labels"] == ["infra"]
    assert "attribute_diff" in d
