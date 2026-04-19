"""Tests for driftwatch.scorer."""
import pytest
from driftwatch.differ import DriftReport, DriftEntry
from driftwatch.scorer import score_report, ScoreReport, _score_entry


def _entry(kind: str, attr_diff=None) -> DriftEntry:
    return DriftEntry(
        resource_id="res-1",
        kind=kind,
        provider="mock",
        resource_type="instance",
        attribute_diff=attr_diff or {},
    )


def _report(*entries) -> DriftReport:
    r = DriftReport()
    for e in entries:
        r.entries.append(e)
    return r


def test_score_empty_report():
    sr = score_report(_report())
    assert sr.total_score == 0.0
    assert sr.entries == []


def test_score_added_entry():
    e = _entry("added")
    s = _score_entry(e)
    assert s == 1.0


def test_score_removed_entry():
    e = _entry("removed")
    s = _score_entry(e)
    assert s == 2.0


def test_score_changed_with_attrs():
    e = _entry("changed", attr_diff={"cpu": {"old": 2, "new": 4}, "ram": {"old": 8, "new": 16}})
    s = _score_entry(e)
    # base 1 + 2 attrs * 0.5 = 2.0
    assert s == 2.0


def test_score_report_sorted_descending():
    entries = [
        _entry("added"),
        _entry("removed"),
        _entry("changed", attr_diff={"x": {"old": 1, "new": 2}}),
    ]
    sr = score_report(_report(*entries))
    scores = [e.score for e in sr.entries]
    assert scores == sorted(scores, reverse=True)


def test_score_report_total():
    entries = [_entry("added"), _entry("removed")]
    sr = score_report(_report(*entries))
    assert sr.total_score == pytest.approx(3.0)


def test_to_dict_structure():
    e = _entry("changed", attr_diff={"k": {"old": "a", "new": "b"}})
    sr = score_report(_report(e))
    d = sr.to_dict()
    assert "total_score" in d
    assert "entries" in d
    assert d["entries"][0]["kind"] == "changed"
    assert d["entries"][0]["changed_attributes"] == 1
