"""Tests for driftwatch.differ_snoozer."""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone

import pytest

from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.differ_snoozer import (
    SnoozeRule,
    SnoozeResult,
    load_rules,
    save_rules,
    snooze_report,
)


def _future(hours: int = 24) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def _past(hours: int = 1) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


def _entry(resource_id: str = "r1", kind: str = "instance", provider: str = "aws") -> DriftEntry:
    return DriftEntry(
        resource_id=resource_id,
        kind=kind,
        provider=provider,
        change_type="changed",
        attribute_diff={},
    )


def _report(*entries: DriftEntry) -> DriftReport:
    r = DriftReport()
    for e in entries:
        r.entries.append(e)
    return r


def test_rule_not_expired_future():
    rule = SnoozeRule(resource_id="r1", until=_future())
    assert not rule.is_expired()


def test_rule_expired_past():
    rule = SnoozeRule(resource_id="r1", until=_past())
    assert rule.is_expired()


def test_rule_matches_by_resource_id():
    rule = SnoozeRule(resource_id="r1", until=_future())
    assert rule.matches(_entry("r1"))
    assert not rule.matches(_entry("r2"))


def test_rule_does_not_match_expired():
    rule = SnoozeRule(resource_id="r1", until=_past())
    assert not rule.matches(_entry("r1"))


def test_rule_matches_with_kind_filter():
    rule = SnoozeRule(resource_id="r1", until=_future(), kind="instance")
    assert rule.matches(_entry("r1", kind="instance"))
    assert not rule.matches(_entry("r1", kind="bucket"))


def test_rule_matches_with_provider_filter():
    rule = SnoozeRule(resource_id="r1", until=_future(), provider="aws")
    assert rule.matches(_entry("r1", provider="aws"))
    assert not rule.matches(_entry("r1", provider="gcp"))


def test_snooze_report_no_rules():
    result = snooze_report(_report(_entry("r1"), _entry("r2")), [])
    assert len(result.active) == 2
    assert len(result.snoozed) == 0


def test_snooze_report_single_match():
    rule = SnoozeRule(resource_id="r1", until=_future())
    result = snooze_report(_report(_entry("r1"), _entry("r2")), [rule])
    assert len(result.snoozed) == 1
    assert result.snoozed[0].resource_id == "r1"
    assert len(result.active) == 1


def test_snooze_report_expired_rule_not_applied():
    rule = SnoozeRule(resource_id="r1", until=_past())
    result = snooze_report(_report(_entry("r1")), [rule])
    assert len(result.active) == 1
    assert len(result.snoozed) == 0


def test_to_dict_structure():
    rule = SnoozeRule(resource_id="r1", until=_future())
    result = snooze_report(_report(_entry("r1"), _entry("r2")), [rule])
    d = result.to_dict()
    assert "snoozed_count" in d
    assert "active_count" in d
    assert d["snoozed_count"] == 1
    assert d["active_count"] == 1


def test_save_and_load_rules(tmp_path):
    rules = [
        SnoozeRule(resource_id="r1", until=_future(), reason="planned", kind="instance"),
        SnoozeRule(resource_id="r2", until=_future(48)),
    ]
    save_rules(rules, directory=str(tmp_path))
    loaded = load_rules(directory=str(tmp_path))
    assert len(loaded) == 2
    assert loaded[0].resource_id == "r1"
    assert loaded[0].reason == "planned"
    assert loaded[1].resource_id == "r2"


def test_load_rules_missing_file(tmp_path):
    result = load_rules(directory=str(tmp_path))
    assert result == []
