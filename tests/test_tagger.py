"""Tests for driftwatch.tagger."""
import pytest
from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.tagger import TagFilter, filter_report, tag_filter_from_dict, _entry_matches


def _entry(kind="changed", tags=None):
    attrs = {"tags": tags or {}}
    return DriftEntry(
        resource_id="res-1",
        provider="aws",
        kind=kind,
        attributes_before=attrs,
        attributes_after=attrs,
        attribute_diff={},
    )


def test_entry_matches_no_filter():
    e = _entry(tags={"env": "prod"})
    tf = TagFilter()
    assert _entry_matches(e, tf) is True


def test_entry_matches_required_pass():
    e = _entry(tags={"env": "prod", "team": "ops"})
    tf = TagFilter(required={"env": "prod"})
    assert _entry_matches(e, tf) is True


def test_entry_matches_required_fail():
    e = _entry(tags={"env": "staging"})
    tf = TagFilter(required={"env": "prod"})
    assert _entry_matches(e, tf) is False


def test_entry_matches_excluded_removes():
    e = _entry(tags={"env": "prod"})
    tf = TagFilter(excluded={"env": "prod"})
    assert _entry_matches(e, tf) is False


def test_entry_matches_excluded_keeps_others():
    e = _entry(tags={"env": "staging"})
    tf = TagFilter(excluded={"env": "prod"})
    assert _entry_matches(e, tf) is True


def test_filter_report_reduces_entries():
    entries = [
        _entry(tags={"env": "prod"}),
        _entry(tags={"env": "staging"}),
    ]
    report = DriftReport(entries=entries)
    tf = TagFilter(required={"env": "prod"})
    filtered = filter_report(report, tf)
    assert len(filtered.entries) == 1
    assert filtered.entries[0].attributes_after["tags"]["env"] == "prod"


def test_filter_report_empty_result():
    entries = [_entry(tags={"env": "dev"})]
    report = DriftReport(entries=entries)
    tf = TagFilter(required={"env": "prod"})
    filtered = filter_report(report, tf)
    assert filtered.entries == []
    assert filtered.has_drift is False


def test_tag_filter_from_dict():
    data = {"required": {"env": "prod"}, "excluded": {"deprecated": "true"}}
    tf = tag_filter_from_dict(data)
    assert tf.required == {"env": "prod"}
    assert tf.excluded == {"deprecated": "true"}


def test_tag_filter_from_dict_defaults():
    tf = tag_filter_from_dict({})
    assert tf.required == {}
    assert tf.excluded == {}
