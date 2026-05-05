"""differ_forecaster.py — predict future drift likelihood based on historical patterns.

Uses a simple linear extrapolation over recent history windows to estimate
how likely a resource is to drift in the next run.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from driftwatch.history import load as load_history


# Resources with forecast scores at or above this threshold are flagged.
DEFAULT_THRESHOLD = 0.5

# Number of most-recent history runs to consider.
DEFAULT_WINDOW = 10


@dataclass
class ForecastEntry:
    """Forecast result for a single resource."""

    resource_id: str
    kind: str
    provider: str
    drift_runs: int        # how many runs in the window contained drift for this resource
    total_runs: int        # total runs in the window
    score: float           # drift_runs / total_runs
    flagged: bool          # score >= threshold

    def to_dict(self) -> dict:
        return {
            "resource_id": self.resource_id,
            "kind": self.kind,
            "provider": self.provider,
            "drift_runs": self.drift_runs,
            "total_runs": self.total_runs,
            "score": round(self.score, 4),
            "flagged": self.flagged,
        }


@dataclass
class ForecastReport:
    """Collection of per-resource forecast entries."""

    entries: List[ForecastEntry] = field(default_factory=list)
    window: int = DEFAULT_WINDOW
    threshold: float = DEFAULT_THRESHOLD

    def flagged(self) -> List[ForecastEntry]:
        """Return only entries whose score meets or exceeds the threshold."""
        return [e for e in self.entries if e.flagged]

    def to_dict(self) -> dict:
        return {
            "window": self.window,
            "threshold": self.threshold,
            "total_resources": len(self.entries),
            "flagged_count": len(self.flagged()),
            "entries": [e.to_dict() for e in self.entries],
        }


def forecast(
    config_path: Optional[str] = None,
    window: int = DEFAULT_WINDOW,
    threshold: float = DEFAULT_THRESHOLD,
) -> ForecastReport:
    """Build a drift-frequency forecast from recent history.

    Args:
        config_path: Optional path override for the history file.
        window:      Number of most-recent runs to examine.
        threshold:   Minimum drift-frequency score to flag a resource.

    Returns:
        A :class:`ForecastReport` with one entry per unique resource seen
        across the window, ranked by descending score.
    """
    history = load_history(config_path)  # list of HistoryEntry
    if not history:
        return ForecastReport(window=window, threshold=threshold)

    # Take the most-recent `window` runs.
    recent = history[-window:]
    total_runs = len(recent)

    # Accumulate per-resource drift counts.
    # Key: (resource_id, kind, provider)
    drift_counts: dict[tuple, int] = {}
    seen_resources: dict[tuple, tuple] = {}  # key -> (resource_id, kind, provider)

    for entry in recent:
        report = entry.report  # DriftReport
        for drift_entry in report.entries:
            key = (drift_entry.resource_id, drift_entry.kind, drift_entry.provider)
            seen_resources[key] = key
            drift_counts[key] = drift_counts.get(key, 0) + 1

    entries: List[ForecastEntry] = []
    for key, count in drift_counts.items():
        resource_id, kind, provider = key
        score = count / total_runs
        entries.append(
            ForecastEntry(
                resource_id=resource_id,
                kind=kind,
                provider=provider,
                drift_runs=count,
                total_runs=total_runs,
                score=score,
                flagged=score >= threshold,
            )
        )

    # Sort by score descending, then resource_id for determinism.
    entries.sort(key=lambda e: (-e.score, e.resource_id))

    return ForecastReport(entries=entries, window=window, threshold=threshold)
