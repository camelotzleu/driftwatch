"""Tests for driftwatch.differ_silencer."""
from datetime import datetime, timedelta, timezone

import pytest

from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.differ_silencer import (
    SilenceRule,
    SilenceResult,
    rules_from_list,
    silence_report,
)


def _entry(resource_id="r-1", kind="instance", provider="aws", change_type="changed"):
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


def _future(days=1):
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def _past(days=1):
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


# --- SilenceRule.is_expired ---

def test_rule_no_until_never_expires():
    rule = SilenceRule(resource_id="r-1")
    assert rule.is_expired() is False


def test_rule_future_until_not_expired():
    rule = SilenceRule(resource_id="r-1", until=_future())
    assert rule.is_expired() is False


def test_rule_past_until_is_expired():
    rule = SilenceRule(resource_id="r-1", until=_past())
    assert rule.is_expired() is True


# --- SilenceRule.matches ---

def test_rule_matches_by_resource_id():
    rule = SilenceRule(resource_id="r-1", until=_future())
    assert rule.matches(_entry("r-1")) is True
    assert rule.matches(_entry("r-2")) is False


def test_rule_matches_by_kind():
    rule = SilenceRule(kind="instance", until=_future())
    assert rule.matches(_entry(kind="instance")) is True
    assert rule.matches(_entry(kind="bucket")) is False


def test_rule_matches_by_provider():
    rule = SilenceRule(provider="gcp", until=_future())
    assert rule.matches(_entry(provider="gcp")) is True
    assert rule.matches(_entry(provider="aws")) is False


def test_expired_rule_never_matches():
    rule = SilenceRule(resource_id="r-1", until=_past())
    assert rule.matches(_entry("r-1")) is False


# --- silence_report ---

def test_silence_empty_report():
    result = silence_report(_report(), [])
    assert result.active == []
    assert result.silenced == []


def test_silence_no_rules_all_active():
    report = _report(_entry("r-1"), _entry("r-2"))
    result = silence_report(report, [])
    assert len(result.active) == 2
    assert len(result.silenced) == 0


def test_silence_matching_rule_moves_entry():
    report = _report(_entry("r-1"), _entry("r-2"))
    rules = [SilenceRule(resource_id="r-1", until=_future())]
    result = silence_report(report, rules)
    assert len(result.active) == 1
    assert result.active[0].resource_id == "r-2"
    assert len(result.silenced) == 1
    assert result.silenced[0].resource_id == "r-1"


def test_silence_expired_rule_leaves_entry_active():
    report = _report(_entry("r-1"))
    rules = [SilenceRule(resource_id="r-1", until=_past())]
    result = silence_report(report, rules)
    assert len(result.active) == 1
    assert len(result.silenced) == 0


def test_silence_rules_applied_count_excludes_expired():
    rules = [
        SilenceRule(resource_id="r-1", until=_future()),
        SilenceRule(resource_id="r-2", until=_past()),
    ]
    result = silence_report(_report(), rules)
    assert result.rules_applied == 1


# --- rules_from_list ---

def test_rules_from_list_builds_rules():
    raw = [{"resource_id": "r-1", "kind": "instance", "until": _future(), "reason": "maintenance"}]
    rules = rules_from_list(raw)
    assert len(rules) == 1
    assert rules[0].resource_id == "r-1"
    assert rules[0].reason == "maintenance"


# --- to_dict ---

def test_silence_result_to_dict():
    result = SilenceResult(active=[_entry()], silenced=[_entry("r-2")], rules_applied=2)
    d = result.to_dict()
    assert d["active_count"] == 1
    assert d["silenced_count"] == 1
    assert d["rules_applied"] == 2
    assert d["silenced"][0]["resource_id"] == "r-2"
