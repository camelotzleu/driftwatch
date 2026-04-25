"""Throttle drift notifications to avoid alert fatigue.

A ThrottleRule suppresses repeated alerts for the same resource within
a configurable cooldown window (in seconds).  The throttle state is
persisted as a JSON file alongside other driftwatch state.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from driftwatch.differ import DriftEntry, DriftReport


def _throttle_path(base_dir: str = ".") -> Path:
    return Path(base_dir) / ".driftwatch" / "throttle_state.json"


@dataclass
class ThrottleRule:
    resource_id: Optional[str] = None
    kind: Optional[str] = None
    provider: Optional[str] = None
    cooldown_seconds: int = 3600

    def matches(self, entry: DriftEntry) -> bool:
        if self.resource_id and entry.resource_id != self.resource_id:
            return False
        if self.kind and entry.kind != self.kind:
            return False
        if self.provider and entry.provider != self.provider:
            return False
        return True


@dataclass
class ThrottleResult:
    allowed: List[DriftEntry] = field(default_factory=list)
    suppressed: List[DriftEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "allowed_count": len(self.allowed),
            "suppressed_count": len(self.suppressed),
            "suppressed_ids": [e.resource_id for e in self.suppressed],
        }


def _load_state(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2))


def throttle_report(
    report: DriftReport,
    rules: List[ThrottleRule],
    base_dir: str = ".",
    now: Optional[float] = None,
) -> ThrottleResult:
    """Filter *report* entries through throttle rules, persisting state."""
    if now is None:
        now = time.time()

    path = _throttle_path(base_dir)
    state: dict = _load_state(path)
    result = ThrottleResult()

    for entry in report.entries:
        suppressed = False
        for rule in rules:
            if not rule.matches(entry):
                continue
            key = f"{entry.provider}:{entry.kind}:{entry.resource_id}"
            last_sent = state.get(key, 0)
            if now - last_sent < rule.cooldown_seconds:
                suppressed = True
                break
            state[key] = now
        if suppressed:
            result.suppressed.append(entry)
        else:
            result.allowed.append(entry)

    _save_state(path, state)
    return result
