"""Baseline management: save and load snapshots to/from disk."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from driftwatch.snapshot import Snapshot

DEFAULT_BASELINE_DIR = ".driftwatch"
DEFAULT_BASELINE_FILE = "baseline.json"


def baseline_path(directory: str = DEFAULT_BASELINE_DIR, filename: str = DEFAULT_BASELINE_FILE) -> Path:
    return Path(directory) / filename


def save(snapshot: Snapshot, path: Optional[Path] = None) -> Path:
    """Persist a snapshot as the current baseline."""
    target = path or baseline_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as fh:
        json.dump(snapshot.to_dict(), fh, indent=2)
    return target


def load(path: Optional[Path] = None) -> Optional[Snapshot]:
    """Load a baseline snapshot from disk. Returns None if file does not exist."""
    target = path or baseline_path()
    if not target.exists():
        return None
    with target.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return Snapshot.from_dict(data)


def exists(path: Optional[Path] = None) -> bool:
    target = path or baseline_path()
    return target.exists()
