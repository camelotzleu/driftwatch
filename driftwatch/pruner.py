"""Baseline pruner: removes stale or outdated baseline snapshots based on age or count."""

from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta
from typing import Optional

from driftwatch.baseline import baseline_path, load as load_baseline, save as save_baseline
from driftwatch.history import load as load_history, history_path


def prune_history_by_age(max_age_days: int, cfg_path: str = ".") -> int:
    """Remove history entries older than max_age_days. Returns count removed."""
    path = history_path(cfg_path)
    if not os.path.exists(path):
        return 0

    entries = load_history(cfg_path)
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    kept = []
    removed = 0
    for entry in entries:
        ts_raw = entry.get("timestamp", "")
        try:
            ts = datetime.fromisoformat(ts_raw)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            kept.append(entry)
            continue
        if ts >= cutoff:
            kept.append(entry)
        else:
            removed += 1

    with open(path, "w") as fh:
        import json
        for e in kept:
            fh.write(json.dumps(e) + "\n")

    return removed


def prune_history_by_count(max_entries: int, cfg_path: str = ".") -> int:
    """Keep only the most recent max_entries history entries. Returns count removed."""
    path = history_path(cfg_path)
    if not os.path.exists(path):
        return 0

    entries = load_history(cfg_path)
    if len(entries) <= max_entries:
        return 0

    removed = len(entries) - max_entries
    kept = entries[-max_entries:]

    import json
    with open(path, "w") as fh:
        for e in kept:
            fh.write(json.dumps(e) + "\n")

    return removed


def prune_baseline_if_stale(max_age_days: int, cfg_path: str = ".") -> bool:
    """Delete the baseline file if it is older than max_age_days. Returns True if removed."""
    path = baseline_path(cfg_path)
    if not os.path.exists(path):
        return False

    mtime = datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    if mtime < cutoff:
        os.remove(path)
        return True
    return False
