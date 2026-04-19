"""Tests for driftwatch.enricher."""
import pytest

from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.enricher import (
    EnrichmentRule,
    enrich_entry,
    enrich_report,
    rules_from_config,
)


def _entry(kind="instance", provider="aws", change_type="changed") -> DriftEntry:
    return DriftEntry(
        resource_id="r-1",
        kind=kind,
        provider=provider,
        change_type=change_type,
        attribute_diff={"type": {"baseline": "t2.micro", "current": "t3.micro"}},
    )


def test_enrich_entry_no_rules():
    e = enrich_entry(_entry(), rules=[])
    assert e.labels == {}
    assert e.notes == []
    assert e.entry.resource_id == "r-1"


def test_enrich_entry_matching_rule():
    rule = EnrichmentRule(match_kind="instance", labels={"team": "ops"}, note="check this")
    e = enrich_entry(_entry(kind="instance"), rules=[rule])
    assert e.labels == {"team": "ops"}
    assert "check this" in e.notes


def test_enrich_entry_non_matching_kind():
    rule = EnrichmentRule(match_kind="bucket", labels={"team": "storage"})
    e = enrich_entry(_entry(kind="instance"), rules=[rule])
    assert e.labels == {}


def test_enrich_entry_non_matching_provider():
    rule = EnrichmentRule(match_provider="gcp", labels={"env": "prod"})
    e = enrich_entry(_entry(provider="aws"), rules=[rule])
    assert e.labels == {}


def test_enrich_entry_multiple_rules_accumulate():
    rules = [
        EnrichmentRule(match_kind="instance", labels={"team": "ops"}, note="note1"),
        EnrichmentRule(match_provider="aws", labels={"cloud": "aws"}, note="note2"),
    ]
    e = enrich_entry(_entry(), rules=rules)
    assert e.labels == {"team": "ops", "cloud": "aws"}
    assert len(e.notes) == 2


def test_enrich_report_returns_all_entries():
    report = DriftReport(
        entries=[_entry("instance"), _entry("bucket", provider="gcp")]
    )
    results = enrich_report(report, rules=[])
    assert len(results) == 2


def test_to_dict_includes_labels_and_notes():
    rule = EnrichmentRule(labels={"x": "y"}, note="hello")
    e = enrich_entry(_entry(), rules=[rule])
    d = e.to_dict()
    assert d["labels"] == {"x": "y"}
    assert "hello" in d["notes"]
    assert "attribute_diff" in d


def test_rules_from_config():
    raw = [
        {"kind": "instance", "provider": "aws", "labels": {"env": "prod"}, "note": "critical"},
        {"kind": "bucket", "labels": {}},
    ]
    rules = rules_from_config(raw)
    assert len(rules) == 2
    assert rules[0].match_kind == "instance"
    assert rules[0].labels == {"env": "prod"}
    assert rules[1].note is None
