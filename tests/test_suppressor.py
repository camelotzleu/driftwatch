"""Tests for driftwatch.suppressor."""
import pytest

from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.suppressor import (
    SuppressionRule,
    suppress_report,
    suppression_rules_from_dict,
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
    r = DriftReport(entries=list(entries))
    return r


def test_suppress_no_rules():
    report = _report(_entry("r1"), _entry("r2"))
    result = suppress_report(report, [])
    assert len(result.kept) == 2
    assert len(result.suppressed) == 0


def test_suppress_by_resource_id():
    report = _report(_entry("r1"), _entry("r2"))
    rules = [SuppressionRule(resource_id="r1")]
    result = suppress_report(report, rules)
    assert len(result.kept) == 1
    assert result.kept[0].resource_id == "r2"
    assert len(result.suppressed) == 1


def test_suppress_by_kind():
    report = _report(_entry("r1", kind="instance"), _entry("r2", kind="bucket"))
    rules = [SuppressionRule(kind="bucket")]
    result = suppress_report(report, rules)
    assert len(result.kept) == 1
    assert result.kept[0].kind == "instance"


def test_suppress_by_provider():
    report = _report(_entry(provider="aws"), _entry("r2", provider="gcp"))
    rules = [SuppressionRule(provider="gcp")]
    result = suppress_report(report, rules)
    assert len(result.kept) == 1
    assert result.kept[0].provider == "aws"


def test_suppress_combined_rule():
    report = _report(
        _entry("r1", kind="instance", provider="aws"),
        _entry("r2", kind="instance", provider="gcp"),
    )
    rules = [SuppressionRule(kind="instance", provider="aws")]
    result = suppress_report(report, rules)
    assert len(result.suppressed) == 1
    assert result.suppressed[0].resource_id == "r1"


def test_to_dict_structure():
    report = _report(_entry("r1"), _entry("r2"))
    rules = [SuppressionRule(resource_id="r1")]
    result = suppress_report(report, rules)
    d = result.to_dict()
    assert d["kept"] == 1
    assert d["suppressed"] == 1
    assert "r1" in d["suppressed_ids"]


def test_suppression_rules_from_dict():
    data = [
        {"resource_id": "r1", "reason": "known issue"},
        {"kind": "bucket", "provider": "aws"},
    ]
    rules = suppression_rules_from_dict(data)
    assert len(rules) == 2
    assert rules[0].resource_id == "r1"
    assert rules[0].reason == "known issue"
    assert rules[1].kind == "bucket"
    assert rules[1].reason == "suppressed"
