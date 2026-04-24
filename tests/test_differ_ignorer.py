"""Tests for driftwatch.differ_ignorer."""
from __future__ import annotations

import pytest

from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.differ_ignorer import (
    IgnoreRule,
    ignore_report,
    ignore_rules_from_list,
)


def _entry(resource_id="res-1", kind="instance", provider="aws", change_type="changed"):
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


# --- IgnoreRule.matches ---

def test_rule_matches_by_resource_id():
    rule = IgnoreRule(resource_id="res-1")
    assert rule.matches(_entry(resource_id="res-1"))
    assert not rule.matches(_entry(resource_id="res-2"))


def test_rule_matches_by_kind():
    rule = IgnoreRule(kind="instance")
    assert rule.matches(_entry(kind="instance"))
    assert not rule.matches(_entry(kind="bucket"))


def test_rule_matches_by_provider():
    rule = IgnoreRule(provider="gcp")
    assert rule.matches(_entry(provider="gcp"))
    assert not rule.matches(_entry(provider="aws"))


def test_rule_matches_combined():
    rule = IgnoreRule(kind="instance", provider="aws")
    assert rule.matches(_entry(kind="instance", provider="aws"))
    assert not rule.matches(_entry(kind="instance", provider="gcp"))


def test_rule_no_criteria_matches_all():
    rule = IgnoreRule()
    assert rule.matches(_entry())


# --- ignore_report ---

def test_ignore_report_no_rules_keeps_all():
    report = _report(_entry("r1"), _entry("r2"))
    result = ignore_report(report, [])
    assert len(result.kept) == 2
    assert len(result.ignored) == 0


def test_ignore_report_removes_matching():
    report = _report(_entry("r1", kind="instance"), _entry("r2", kind="bucket"))
    rules = [IgnoreRule(kind="instance", reason="planned")]
    result = ignore_report(report, rules)
    assert len(result.kept) == 1
    assert result.kept[0].resource_id == "r2"
    assert len(result.ignored) == 1
    assert result.ignored_reasons["r1"] == "planned"


def test_ignore_report_to_dict_structure():
    report = _report(_entry("r1"))
    rules = [IgnoreRule(resource_id="r1", reason="test")]
    result = ignore_report(report, rules)
    d = result.to_dict()
    assert d["kept_count"] == 0
    assert d["ignored_count"] == 1
    assert d["ignored"][0]["resource_id"] == "r1"
    assert d["ignored"][0]["reason"] == "test"


# --- ignore_rules_from_list ---

def test_ignore_rules_from_list_empty():
    assert ignore_rules_from_list([]) == []


def test_ignore_rules_from_list_parses_fields():
    raw = [{"resource_id": "r1", "kind": "instance", "provider": "aws", "reason": "ok"}]
    rules = ignore_rules_from_list(raw)
    assert len(rules) == 1
    assert rules[0].resource_id == "r1"
    assert rules[0].reason == "ok"


def test_ignore_rules_from_list_partial_fields():
    raw = [{"kind": "bucket"}]
    rules = ignore_rules_from_list(raw)
    assert rules[0].resource_id is None
    assert rules[0].kind == "bucket"
    assert rules[0].reason == ""
