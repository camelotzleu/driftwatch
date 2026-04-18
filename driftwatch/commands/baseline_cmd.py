"""CLI command implementations for baseline management."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from driftwatch import baseline as baseline_mod
from driftwatch.snapshot import Snapshot


def cmd_baseline_save(snapshot: Snapshot, path: Optional[Path] = None, quiet: bool = False) -> int:
    """Save snapshot as baseline. Returns exit code."""
    try:
        saved_path = baseline_mod.save(snapshot, path=path)
        if not quiet:
            print(f"Baseline saved to {saved_path} ({len(snapshot.resources)} resource(s)).")
        return 0
    except OSError as exc:
        print(f"Error saving baseline: {exc}", file=sys.stderr)
        return 1


def cmd_baseline_show(path: Optional[Path] = None) -> int:
    """Print a summary of the current baseline. Returns exit code."""
    snap = baseline_mod.load(path=path)
    if snap is None:
        print("No baseline found. Run 'driftwatch baseline save' first.")
        return 1
    print(f"Baseline contains {len(snap.resources)} resource(s):")
    for r in sorted(snap.resources, key=lambda x: (x.provider, x.resource_type, x.resource_id)):
        print(f"  [{r.provider}] {r.resource_type}/{r.resource_id}")
    return 0


def cmd_baseline_clear(path: Optional[Path] = None, quiet: bool = False) -> int:
    """Delete the baseline file. Returns exit code."""
    target = path or baseline_mod.baseline_path()
    if not target.exists():
        if not quiet:
            print("No baseline file to remove.")
        return 0
    try:
        target.unlink()
        if not quiet:
            print(f"Baseline removed: {target}")
        return 0
    except OSError as exc:
        print(f"Error removing baseline: {exc}", file=sys.stderr)
        return 1
