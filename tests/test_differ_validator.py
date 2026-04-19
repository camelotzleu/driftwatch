"""Tests for differ_validator module."""
import pytest
from driftwatch.differ import DriftReport, DriftEntry
from driftwatch.differ_validator import (
    ValidationRule,
    validate_report,
    validation_rules_from_dict,
    ValidationReport,
)


def _entry(resource_id="r1", kind="instance", provider="aws", change_type="changed"):
    return DriftEntry(
        resource_id=resource_id,
        kind=kind,
        provider=provider,
        change_type=change_type,
        attribute_diff={},
    )


def _report(*entries):
    r = DriftReport()
    for e in entries:
        r.entries.append(e)
    return r


def test_validate_empty_report():
    rules = [ValidationRule(field="kind", allowed_values=["instance"])]
    result = validate_report(_report(), rules)
    assert result.valid
    assert result.violations == []


def test_validate_no_rules():
    result = validate_report(_report(_entry()), [])
    assert result.valid


def test_validate_passing_entry():
    rules = [ValidationRule(field="kind", allowed_values=["instance", "bucket"])]
    result = validate_report(_report(_entry(kind="instance")), rules)
    assert result.valid


def test_validate_violation_kind():
    rules = [ValidationRule(field="kind", allowed_values=["bucket"])]
    result = validate_report(_report(_entry(kind="instance")), rules)
    assert not result.valid
    assert len(result.violations) == 1
    assert result.violations[0].actual_value == "instance"
    assert result.violations[0].rule.field == "kind"


def test_validate_violation_provider():
    rules = [ValidationRule(field="provider", allowed_values=["gcp"])]
    result = validate_report(_report(_entry(provider="aws")), rules)
    assert not result.valid
    assert result.violations[0].actual_value == "aws"


def test_validate_multiple_entries_mixed():
    rules = [ValidationRule(field="kind", allowed_values=["instance"])]
    report = _report(_entry(kind="instance"), _entry(kind="disk"), _entry(kind="instance"))
    result = validate_report(report, rules)
    assert not result.valid
    assert len(result.violations) == 1


def test_to_dict_structure():
    rules = [ValidationRule(field="kind", allowed_values=["bucket"], message="only buckets")]
    result = validate_report(_report(_entry(kind="instance")), rules)
    d = result.to_dict()
    assert d["valid"] is False
    assert d["violation_count"] == 1
    v = d["violations"][0]
    assert v["field"] == "kind"
    assert v["actual"] == "instance"
    assert v["message"] == "only buckets"


def test_rules_from_dict():
    data = {
        "validation_rules": [
            {"field": "kind", "allowed_values": ["instance"], "message": "ok"},
            {"field": "provider", "allowed_values": ["aws", "gcp"]},
        ]
    }
    rules = validation_rules_from_dict(data)
    assert len(rules) == 2
    assert rules[0].field == "kind"
    assert rules[1].allowed_values == ["aws", "gcp"]
    assert rules[1].message is None


def test_rules_from_dict_empty():
    rules = validation_rules_from_dict({})
    assert rules == []
