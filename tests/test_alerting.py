"""Tests for driftwatch.alerting."""
import pytest
from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.alerting import AlertRule, evaluate, rules_from_dict


def _entry(provider="aws", resource_type="ec2", kind="changed"):
    return DriftEntry(
        resource_id=f"{provider}-res-1",
        resource_type=resource_type,
        provider=provider,
        kind=kind,
        attribute_diff={"instance_type": {"baseline": "t2.micro", "current": "t3.small"}},
    )


def _report(*entries):
    r = DriftReport()
    for e in entries:
        r.entries.append(e)
    return r


def test_evaluate_no_rules():
    report = _report(_entry())
    results = evaluate(report, [])
    assert results == []


def test_evaluate_rule_triggered():
    rule = AlertRule(name="any-change", min_changes=1)
    report = _report(_entry(), _entry(provider="gcp"))
    results = evaluate(report, [rule])
    assert len(results) == 1
    assert results[0].triggered
    assert results[0].severity == "warning"


def test_evaluate_rule_not_triggered_below_threshold():
    rule = AlertRule(name="many-changes", min_changes=5)
    report = _report(_entry())
    results = evaluate(report, [rule])
    assert not results[0].triggered


def test_evaluate_filters_by_provider():
    rule = AlertRule(name="aws-only", providers=["aws"])
    report = _report(_entry(provider="aws"), _entry(provider="gcp"))
    results = evaluate(report, [rule])
    assert len(results[0].matched_entries) == 1
    assert results[0].matched_entries[0].provider == "aws"


def test_evaluate_filters_by_resource_type():
    rule = AlertRule(name="ec2-only", resource_types=["ec2"])
    report = _report(_entry(resource_type="ec2"), _entry(resource_type="s3"))
    results = evaluate(report, [rule])
    assert len(results[0].matched_entries) == 1


def test_rules_from_dict():
    data = [
        {"name": "critical-rule", "min_changes": 3, "providers": ["aws"], "severity": "critical"},
        {"name": "info-rule"},
    ]
    rules = rules_from_dict(data)
    assert len(rules) == 2
    assert rules[0].name == "critical-rule"
    assert rules[0].min_changes == 3
    assert rules[0].severity == "critical"
    assert rules[1].severity == "warning"


def test_evaluate_empty_report():
    rule = AlertRule(name="any", min_changes=1)
    results = evaluate(_report(), [rule])
    assert not results[0].triggered
