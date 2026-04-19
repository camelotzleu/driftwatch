"""Tests for driftwatch.differ_trend."""
from __future__ import annotations

from unittest.mock import patch

from driftwatch.differ_trend import analyze_trend, _classify, TrendEntry


def _run(entries):
    """Build a minimal history run dict."""
    return {"report": {"entries": entries}}


def _e(rid, provider="aws", kind="ec2"):
    return {"resource_id": rid, "provider": provider, "kind": kind}


# ---------------------------------------------------------------------------
# _classify
# ---------------------------------------------------------------------------

def test_classify_rising():
    assert _classify([1, 2, 3]) == "rising"


def test_classify_falling():
    assert _classify([3, 2, 1]) == "falling"


def test_classify_stable():
    assert _classify([2, 2, 2]) == "stable"


def test_classify_single():
    assert _classify([5]) == "stable"


# ---------------------------------------------------------------------------
# analyze_trend
# ---------------------------------------------------------------------------

def test_analyze_trend_empty_history():
    with patch("driftwatch.differ_trend.load_history", return_value=[]):
        report = analyze_trend(windows=3)
    assert report.windows == 3
    assert report.entries == []


def test_analyze_trend_returns_trend_report():
    history = [
        _run([_e("res-1")]),
        _run([_e("res-1")]),
        _run([_e("res-1"), _e("res-2")]),
    ]
    with patch("driftwatch.differ_trend.load_history", return_value=history):
        report = analyze_trend(windows=3)
    assert report.windows == 3
    ids = {e.resource_id for e in report.entries}
    assert "res-1" in ids


def test_analyze_trend_to_dict():
    history = [_run([_e("r1")]), _run([_e("r1")]), _run([_e("r1")])]
    with patch("driftwatch.differ_trend.load_history", return_value=history):
        report = analyze_trend(windows=3)
    d = report.to_dict()
    assert "windows" in d
    assert "entries" in d
    assert isinstance(d["entries"], list)


def test_trend_entry_to_dict():
    e = TrendEntry(
        resource_id="r1",
        provider="gcp",
        kind="compute",
        drift_counts=[0, 1, 3],
        trend="rising",
    )
    d = e.to_dict()
    assert d["trend"] == "rising"
    assert d["drift_counts"] == [0, 1, 3]
    assert d["provider"] == "gcp"


def test_analyze_trend_meta_captured():
    history = [_run([_e("r1", "azure", "vm")]), _run([]), _run([])]
    with patch("driftwatch.differ_trend.load_history", return_value=history):
        report = analyze_trend(windows=3)
    entry = next((e for e in report.entries if e.resource_id == "r1"), None)
    assert entry is not None
    assert entry.provider == "azure"
    assert entry.kind == "vm"
