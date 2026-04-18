import pytest
from unittest.mock import MagicMock, patch

from driftwatch.scheduler import _run_once, run_scheduler
from driftwatch.config import DriftWatchConfig, ProviderConfig
from driftwatch.snapshot import Snapshot
from driftwatch.differ import DriftReport


def _cfg():
    return DriftWatchConfig(provider=ProviderConfig(name="mock", credentials={}))


def _empty_report(has_drift=False):
    report = MagicMock(spec=DriftReport)
    report.has_drift.return_value = has_drift
    return report


@patch("driftwatch.scheduler.render", return_value="ok")
@patch("driftwatch.scheduler.compare")
@patch("driftwatch.scheduler.load_baseline")
@patch("driftwatch.scheduler.get_collector")
def test_run_once_no_baseline_saves(mock_gc, mock_lb, mock_cmp, mock_render):
    mock_lb.return_value = None
    collector = MagicMock()
    collector.collect.return_value = Snapshot(provider="mock", region="global")
    mock_gc.return_value = collector
    with patch("driftwatch.scheduler.save_baseline") as mock_save:
        result = _run_once(_cfg(), "text")
    mock_save.assert_called_once()
    mock_cmp.assert_not_called()
    assert result is False


@patch("driftwatch.scheduler.render", return_value="report")
@patch("driftwatch.scheduler.compare")
@patch("driftwatch.scheduler.load_baseline")
@patch("driftwatch.scheduler.get_collector")
def test_run_once_with_baseline_compares(mock_gc, mock_lb, mock_cmp, mock_render):
    baseline = Snapshot(provider="mock", region="global")
    mock_lb.return_value = baseline
    current = Snapshot(provider="mock", region="global")
    collector = MagicMock()
    collector.collect.return_value = current
    mock_gc.return_value = collector
    mock_cmp.return_value = _empty_report(has_drift=False)
    result = _run_once(_cfg(), "text")
    mock_cmp.assert_called_once_with(baseline, current)
    assert result is False


@patch("driftwatch.scheduler.render", return_value="report")
@patch("driftwatch.scheduler.compare")
@patch("driftwatch.scheduler.load_baseline")
@patch("driftwatch.scheduler.get_collector")
def test_run_once_calls_on_drift(mock_gc, mock_lb, mock_cmp, mock_render):
    mock_lb.return_value = Snapshot(provider="mock", region="global")
    collector = MagicMock()
    collector.collect.return_value = Snapshot(provider="mock", region="global")
    mock_gc.return_value = collector
    report = _empty_report(has_drift=True)
    mock_cmp.return_value = report
    cb = MagicMock()
    _run_once(_cfg(), "text", on_drift=cb)
    cb.assert_called_once_with(report)


@patch("driftwatch.scheduler.time.sleep")
@patch("driftwatch.scheduler._run_once", return_value=False)
def test_run_scheduler_respects_max_iterations(mock_run, mock_sleep):
    run_scheduler(_cfg(), interval=10, max_iterations=3)
    assert mock_run.call_count == 3
    assert mock_sleep.call_count == 2


@patch("driftwatch.scheduler.time.sleep")
@patch("driftwatch.scheduler._run_once", side_effect=RuntimeError("boom"))
def test_run_scheduler_handles_errors(mock_run, mock_sleep):
    run_scheduler(_cfg(), interval=5, max_iterations=2)
    assert mock_run.call_count == 2
