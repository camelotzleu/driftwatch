"""Tests for driftwatch.differ_throttler."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.differ_throttler import (
    ThrottleRule,
    ThrottleResult,
    _throttle_path,
    throttle_report,
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


# ---------------------------------------------------------------------------
# ThrottleRule.matches
# ---------------------------------------------------------------------------

def test_rule_matches_by_resource_id():
    rule = ThrottleRule(resource_id="r1")
    assert rule.matches(_entry(resource_id="r1"))
    assert not rule.matches(_entry(resource_id="r2"))


def test_rule_matches_by_kind():
    rule = ThrottleRule(kind="instance")
    assert rule.matches(_entry(kind="instance"))
    assert not rule.matches(_entry(kind="bucket"))


def test_rule_matches_by_provider():
    rule = ThrottleRule(provider="aws")
    assert rule.matches(_entry(provider="aws"))
    assert not rule.matches(_entry(provider="gcp"))


def test_rule_no_filters_matches_all():
    rule = ThrottleRule()
    assert rule.matches(_entry())


# ---------------------------------------------------------------------------
# throttle_report — no rules
# ---------------------------------------------------------------------------

def test_throttle_no_rules_allows_all(tmp_path):
    report = _report(_entry("r1"), _entry("r2"))
    result = throttle_report(report, rules=[], base_dir=str(tmp_path))
    assert len(result.allowed) == 2
    assert len(result.suppressed) == 0


# ---------------------------------------------------------------------------
# throttle_report — first call always allowed
# ---------------------------------------------------------------------------

def test_throttle_first_call_allowed(tmp_path):
    rule = ThrottleRule(kind="instance", cooldown_seconds=3600)
    report = _report(_entry("r1"))
    result = throttle_report(report, [rule], base_dir=str(tmp_path), now=1_000_000)
    assert len(result.allowed) == 1
    assert len(result.suppressed) == 0


# ---------------------------------------------------------------------------
# throttle_report — second call within cooldown is suppressed
# ---------------------------------------------------------------------------

def test_throttle_second_call_suppressed(tmp_path):
    rule = ThrottleRule(kind="instance", cooldown_seconds=3600)
    report = _report(_entry("r1"))
    t0 = 1_000_000
    throttle_report(report, [rule], base_dir=str(tmp_path), now=t0)
    result = throttle_report(report, [rule], base_dir=str(tmp_path), now=t0 + 60)
    assert len(result.suppressed) == 1
    assert len(result.allowed) == 0


# ---------------------------------------------------------------------------
# throttle_report — call after cooldown expires is allowed again
# ---------------------------------------------------------------------------

def test_throttle_after_cooldown_allowed(tmp_path):
    rule = ThrottleRule(kind="instance", cooldown_seconds=3600)
    report = _report(_entry("r1"))
    t0 = 1_000_000
    throttle_report(report, [rule], base_dir=str(tmp_path), now=t0)
    result = throttle_report(report, [rule], base_dir=str(tmp_path), now=t0 + 7200)
    assert len(result.allowed) == 1
    assert len(result.suppressed) == 0


# ---------------------------------------------------------------------------
# ThrottleResult.to_dict
# ---------------------------------------------------------------------------

def test_to_dict_structure(tmp_path):
    rule = ThrottleRule(kind="instance", cooldown_seconds=3600)
    report = _report(_entry("r1"), _entry("r2"))
    t0 = 1_000_000
    throttle_report(report, [rule], base_dir=str(tmp_path), now=t0)
    result = throttle_report(report, [rule], base_dir=str(tmp_path), now=t0 + 60)
    d = result.to_dict()
    assert d["suppressed_count"] == 2
    assert "r1" in d["suppressed_ids"]


# ---------------------------------------------------------------------------
# State file is created
# ---------------------------------------------------------------------------

def test_state_file_created(tmp_path):
    rule = ThrottleRule(kind="instance", cooldown_seconds=3600)
    report = _report(_entry("r1"))
    throttle_report(report, [rule], base_dir=str(tmp_path), now=1_000_000)
    state_path = _throttle_path(str(tmp_path))
    assert state_path.exists()
    data = json.loads(state_path.read_text())
    assert any("r1" in k for k in data)
