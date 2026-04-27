"""Tests for driftwatch/differ_changelog.py"""
from __future__ import annotations

import json
from unittest.mock import patch

from driftwatch.differ_changelog import (
    ChangelogEntry,
    ChangelogReport,
    _summary_for,
    build_changelog,
)


def _run(run_id="r1", timestamp="2024-01-01T00:00:00", entries=None):
    return {
        "run_id": run_id,
        "timestamp": timestamp,
        "drift": {"entries": entries or []},
    }


def _entry(resource_id="i-123", kind="ec2", provider="aws", change_type="changed", attr_diff=None):
    e = {
        "resource_id": resource_id,
        "kind": kind,
        "provider": provider,
        "change_type": change_type,
    }
    if attr_diff is not None:
        e["attribute_diff"] = attr_diff
    return e


def test_build_changelog_empty_history():
    with patch("driftwatch.differ_changelog.load_history", return_value=[]):
        report = build_changelog()
    assert isinstance(report, ChangelogReport)
    assert report.entries == []


def test_build_changelog_single_run():
    history = [_run(entries=[_entry(change_type="added")])]
    with patch("driftwatch.differ_changelog.load_history", return_value=history):
        report = build_changelog()
    assert len(report.entries) == 1
    e = report.entries[0]
    assert e.run_id == "r1"
    assert e.change_type == "added"
    assert e.provider == "aws"
    assert e.resource_id == "i-123"


def test_build_changelog_provider_filter():
    history = [
        _run(entries=[_entry(provider="aws"), _entry(provider="gcp", resource_id="g-1")])
    ]
    with patch("driftwatch.differ_changelog.load_history", return_value=history):
        report = build_changelog(provider_filter="aws")
    assert len(report.entries) == 1
    assert report.entries[0].provider == "aws"


def test_build_changelog_limit():
    entries = [_entry(resource_id=f"i-{i}") for i in range(5)]
    history = [_run(entries=entries)]
    with patch("driftwatch.differ_changelog.load_history", return_value=history):
        report = build_changelog(limit=3)
    assert len(report.entries) == 3
    assert report.entries[-1].resource_id == "i-4"


def test_summary_for_added():
    assert "appeared" in _summary_for({"change_type": "added"})


def test_summary_for_removed():
    assert "disappeared" in _summary_for({"change_type": "removed"})


def test_summary_for_changed_with_attr_diff():
    s = _summary_for({"change_type": "changed", "attribute_diff": {"state": {}, "type": {}}})
    assert "state" in s
    assert "type" in s


def test_to_dict_structure():
    history = [_run(entries=[_entry(change_type="removed")])]
    with patch("driftwatch.differ_changelog.load_history", return_value=history):
        report = build_changelog()
    d = report.to_dict()
    assert "entries" in d
    assert d["entries"][0]["change_type"] == "removed"


def test_to_text_no_entries():
    report = ChangelogReport()
    assert "No changes" in report.to_text()


def test_to_text_contains_resource_id():
    history = [_run(entries=[_entry(resource_id="i-999", change_type="added")])]
    with patch("driftwatch.differ_changelog.load_history", return_value=history):
        report = build_changelog()
    text = report.to_text()
    assert "i-999" in text
    assert "ADDED" in text
