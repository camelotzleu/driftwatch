"""Trend analysis: detect resources whose drift frequency is increasing over time."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

from driftwatch.history import load as load_history


@dataclass
class TrendEntry:
    resource_id: str
    provider: str
    kind: str
    drift_counts: List[int]  # count per window (oldest -> newest)
    trend: str  # "rising", "falling", "stable"

    def to_dict(self) -> dict:
        return {
            "resource_id": self.resource_id,
            "provider": self.provider,
            "kind": self.kind,
            "drift_counts": self.drift_counts,
            "trend": self.trend,
        }


@dataclass
class TrendReport:
    windows: int
    entries: List[TrendEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "windows": self.windows,
            "entries": [e.to_dict() for e in self.entries],
        }


def _classify(counts: List[int]) -> str:
    if len(counts) < 2:
        return "stable"
    if counts[-1] > counts[0]:
        return "rising"
    if counts[-1] < counts[0]:
        return "falling"
    return "stable"


def analyze_trend(windows: int = 3, config_path: str | None = None) -> TrendReport:
    """Split history into *windows* equal buckets and count drift per resource."""
    history = load_history(config_path)
    if not history:
        return TrendReport(windows=windows)

    bucket_size = max(1, len(history) // windows)
    buckets = [
        history[i * bucket_size: (i + 1) * bucket_size]
        for i in range(windows)
    ]

    # resource key -> list of per-bucket counts
    counts: Dict[str, List[int]] = {}
    meta: Dict[str, dict] = {}

    for bucket in buckets:
        bucket_counts: Dict[str, int] = {}
        for run in bucket:
            report = run.get("report", {})
            for entry in report.get("entries", []):
                key = entry.get("resource_id", "unknown")
                bucket_counts[key] = bucket_counts.get(key, 0) + 1
                if key not in meta:
                    meta[key] = {
                        "provider": entry.get("provider", ""),
                        "kind": entry.get("kind", ""),
                    }
        for key, cnt in bucket_counts.items():
            counts.setdefault(key, [0] * windows)
        for key in counts:
            counts[key].append(bucket_counts.get(key, 0))

    entries = []
    for key, drift_counts in counts.items():
        dc = drift_counts[:windows]
        entries.append(TrendEntry(
            resource_id=key,
            provider=meta.get(key, {}).get("provider", ""),
            kind=meta.get(key, {}).get("kind", ""),
            drift_counts=dc,
            trend=_classify(dc),
        ))

    entries.sort(key=lambda e: e.drift_counts[-1], reverse=True)
    return TrendReport(windows=windows, entries=entries)
