"""Tests for driftwatch.differ_normalizer."""
import pytest
from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.differ_normalizer import normalize_report, _normalize_value


def _entry(resource_id="r1", kind="VM", provider="aws", change_type="changed", attribute_diff=None):
    return DriftEntry(
        resource_id=resource_id,
        kind=kind,
        provider=provider,
        change_type=change_type,
        attribute_diff=attribute_diff or {},
    )


def _report(*entries):
    return DriftReport(entries=list(entries))


def test_normalize_value_strips_whitespace():
    val, desc = _normalize_value("  hello  ")
    assert val == "hello"
    assert desc is not None


def test_normalize_value_lowercases():
    val, desc = _normalize_value("Hello")
    assert val == "hello"
    assert desc is not None


def test_normalize_value_no_change_clean_string():
    val, desc = _normalize_value("hello")
    assert val == "hello"
    assert desc is None


def test_normalize_value_float_to_int():
    val, desc = _normalize_value(2.0)
    assert val == 2
    assert isinstance(val, int)
    assert desc is not None


def test_normalize_value_float_stays_float():
    val, desc = _normalize_value(2.5)
    assert val == 2.5
    assert desc is None


def test_normalize_empty_report():
    report = _report()
    result = normalize_report(report)
    assert result.entries == []


def test_normalize_entry_no_attribute_diff():
    report = _report(_entry())
    result = normalize_report(report)
    assert len(result.entries) == 1
    assert result.entries[0].changes == {}


def test_normalize_entry_records_change():
    e = _entry(attribute_diff={"region": {"before": "US-EAST", "after": "us-east"}})
    result = normalize_report(_report(e))
    ne = result.entries[0]
    assert "region.before" in ne.changes


def test_normalize_entry_mutates_diff_value():
    e = _entry(attribute_diff={"name": {"before": "  MyVM  ", "after": "myvm"}})
    normalize_report(_report(e))
    assert e.attribute_diff["name"]["before"] == "myvm"


def test_to_dict_structure():
    e = _entry(attribute_diff={"size": {"before": 4.0, "after": 8.0}})
    result = normalize_report(_report(e))
    d = result.to_dict()
    assert "normalized" in d
    assert d["normalized"][0]["resource_id"] == "r1"
    assert "normalizations" in d["normalized"][0]
