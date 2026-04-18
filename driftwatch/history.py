"""Drift history tracking — persists DriftReport entries to a local JSONL log."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from driftwatch.differ import DriftReport

DEFAULT_HISTORY_PATH = Path(".driftwatch") / "history.jsonl"


def history_path(override: Optional[str] = None) -> Path:
    if override:
        return Path(override)
    return DEFAULT_HISTORY_PATH


def append(report: DriftReport, path: Optional[Path] = None) -> Path:
    """Append a DriftReport as a timestamped JSONL entry."""
    target = path or history_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "has_drift": report.has_drift,
        "summary": report.summary(),
        "changed": [_entry_to_dict(e) for e in report.changed],
        "added": [_entry_to_dict(e) for e in report.added],
        "removed": [_entry_to_dict(e) for e in report.removed],
    }
    with target.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
    return target


def load(path: Optional[Path] = None, limit: int = 100) -> List[dict]:
    """Return up to *limit* most-recent history entries (newest first)."""
    target = path or history_path()
    if not target.exists():
        return []
    lines = target.read_text(encoding="utf-8").splitlines()
    entries = []
    for line in lines:
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return list(reversed(entries[-limit:]))


def clear(path: Optional[Path] = None) -> None:
    """Delete the history file."""
    target = path or history_path()
    if target.exists():
        target.unlink()


def _entry_to_dict(entry) -> dict:
    return {
        "resource_id": entry.resource_id,
        "provider": entry.provider,
        "kind": entry.kind,
        "attribute_diff": entry.attribute_diff,
    }
