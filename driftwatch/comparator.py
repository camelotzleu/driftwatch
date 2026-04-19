"""Baseline comparison utilities for DriftWatch."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from driftwatch.baseline import load as load_baseline
from driftwatch.differ import DriftReport, compare
from driftwatch.snapshot import Snapshot


@dataclass
class CompareResult:
    report: Optional[DriftReport]
    baseline_missing: bool = False
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None and not self.baseline_missing


def compare_to_baseline(current: Snapshot, config_dir: str = ".") -> CompareResult:
    """Compare *current* snapshot against the saved baseline.

    Returns a :class:`CompareResult` describing the outcome.
    """
    baseline = load_baseline(config_dir=config_dir)
    if baseline is None:
        return CompareResult(report=None, baseline_missing=True)
    try:
        report = compare(baseline, current)
    except Exception as exc:  # pragma: no cover
        return CompareResult(report=None, error=str(exc))
    return CompareResult(report=report)


def compare_snapshots(old: Snapshot, new: Snapshot) -> DriftReport:
    """Thin wrapper so callers don't need to import differ directly."""
    return compare(old, new)
