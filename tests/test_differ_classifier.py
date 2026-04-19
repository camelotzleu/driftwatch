"""Tests for driftwatch.differ_classifier."""
import pytest
from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.differ_classifier import (
    classify_report,
    _classify_entry,
    ClassificationReport,
)


def _entry(change_type="changed", attr_diff=None):
    return DriftEntry(
        resource_id="res-1",
        kind="instance",
        provider="aws",
        change_type=change_type,
        attribute_diff=attr_diff,
    )


def _report(*entries):
    r = DriftReport()
    for e in entries:
        r.entries.append(e)
    return r


def test_classify_added_is_high():
    assert _classify_entry(_entry("added")) == "high"


def test_classify_removed_is_high():
    assert _classify_entry(_entry("removed")) == "high"


def test_classify_high_impact_key():
    e = _entry("changed", {"instance_type": {"before": "t2.micro", "after": "t3.large"}})
    assert _classify_entry(e) == "high"


def test_classify_medium_impact_key():
    e = _entry("changed", {"tags": {"before": {}, "after": {"env": "prod"}}})
    assert _classify_entry(e) == "medium"


def test_classify_low_impact_key():
    e = _entry("changed", {"description": {"before": "old", "after": "new"}})
    assert _classify_entry(e) == "low"


def test_classify_empty_diff_is_low():
    e = _entry("changed", {})
    assert _classify_entry(e) == "low"


def test_classify_report_empty():
    r = classify_report(_report())
    assert isinstance(r, ClassificationReport)
    assert r.entries == []


def test_classify_report_counts():
    r = classify_report(_report(
        _entry("added"),
        _entry("changed", {"tags": {}}),
        _entry("changed", {"description": {}}),
    ))
    d = r.to_dict()
    assert d["counts"]["high"] == 1
    assert d["counts"]["medium"] == 1
    assert d["counts"]["low"] == 1
    assert d["total"] == 3


def test_to_dict_entry_fields():
    r = classify_report(_report(_entry("added")))
    entry_dict = r.to_dict()["entries"][0]
    assert entry_dict["resource_id"] == "res-1"
    assert entry_dict["impact"] == "high"
    assert entry_dict["change_type"] == "added"


def test_high_beats_medium_when_both_present():
    e = _entry("changed", {"instance_type": {}, "tags": {}})
    assert _classify_entry(e) == "high"
