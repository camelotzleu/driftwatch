"""Tests for driftwatch.differ_acknowledger."""
import json
import pytest

from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.differ_acknowledger import (
    AckRule,
    AckReport,
    acknowledge_report,
    load_ack_rules,
    save_ack_rules,
    _ack_path,
)


def _entry(
    resource_id: str = "res-1",
    kind: str = "instance",
    provider: str = "aws",
    change_type: str = "changed",
) -> DriftEntry:
    return DriftEntry(
        resource_id=resource_id,
        kind=kind,
        provider=provider,
        change_type=change_type,
        attribute_diff={},
    )


def _report(*entries: DriftEntry) -> DriftReport:
    r = DriftReport()
    for e in entries:
        r.entries.append(e)
    return r


# ---------------------------------------------------------------------------
# AckRule.matches
# ---------------------------------------------------------------------------

def test_rule_matches_by_resource_id():
    rule = AckRule(resource_id="res-1")
    assert rule.matches(_entry(resource_id="res-1"))
    assert not rule.matches(_entry(resource_id="res-2"))


def test_rule_matches_with_kind_filter():
    rule = AckRule(resource_id="res-1", kind="instance")
    assert rule.matches(_entry(resource_id="res-1", kind="instance"))
    assert not rule.matches(_entry(resource_id="res-1", kind="bucket"))


def test_rule_matches_with_provider_filter():
    rule = AckRule(resource_id="res-1", provider="aws")
    assert rule.matches(_entry(resource_id="res-1", provider="aws"))
    assert not rule.matches(_entry(resource_id="res-1", provider="gcp"))


# ---------------------------------------------------------------------------
# acknowledge_report
# ---------------------------------------------------------------------------

def test_acknowledge_empty_report():
    result = acknowledge_report(_report(), [])
    assert result.acknowledged == []
    assert result.unacknowledged == []


def test_acknowledge_no_rules():
    e = _entry()
    result = acknowledge_report(_report(e), [])
    assert len(result.unacknowledged) == 1
    assert len(result.acknowledged) == 0


def test_acknowledge_matching_entry():
    e = _entry(resource_id="res-1")
    rule = AckRule(resource_id="res-1", reason="known issue")
    result = acknowledge_report(_report(e), [rule])
    assert len(result.acknowledged) == 1
    assert result.acknowledged[0].reason == "known issue"
    assert len(result.unacknowledged) == 0


def test_acknowledge_partial_match():
    e1 = _entry(resource_id="res-1")
    e2 = _entry(resource_id="res-2")
    rule = AckRule(resource_id="res-1", reason="ok")
    result = acknowledge_report(_report(e1, e2), [rule])
    assert len(result.acknowledged) == 1
    assert len(result.unacknowledged) == 1
    assert result.unacknowledged[0].resource_id == "res-2"


def test_to_dict_structure():
    e = _entry(resource_id="res-1")
    rule = AckRule(resource_id="res-1", reason="planned")
    result = acknowledge_report(_report(e), [rule])
    d = result.to_dict()
    assert d["total"] == 1
    assert d["acknowledged_count"] == 1
    assert d["unacknowledged_count"] == 0
    assert d["acknowledged"][0]["reason"] == "planned"


# ---------------------------------------------------------------------------
# save / load round-trip
# ---------------------------------------------------------------------------

def test_save_and_load_rules(tmp_path):
    rules = [
        AckRule(resource_id="res-1", kind="instance", provider="aws", reason="ok"),
        AckRule(resource_id="res-2", reason="planned maintenance"),
    ]
    save_ack_rules(rules, base_dir=str(tmp_path))
    loaded = load_ack_rules(base_dir=str(tmp_path))
    assert len(loaded) == 2
    assert loaded[0].resource_id == "res-1"
    assert loaded[0].kind == "instance"
    assert loaded[1].reason == "planned maintenance"


def test_load_returns_empty_when_no_file(tmp_path):
    rules = load_ack_rules(base_dir=str(tmp_path))
    assert rules == []


def test_save_creates_valid_json(tmp_path):
    rules = [AckRule(resource_id="r", reason="test")]
    save_ack_rules(rules, base_dir=str(tmp_path))
    path = _ack_path(str(tmp_path))
    with path.open() as fh:
        data = json.load(fh)
    assert isinstance(data, list)
    assert data[0]["resource_id"] == "r"
