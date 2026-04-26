"""Snooze (temporarily suppress) drift entries for a fixed duration."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from driftwatch.differ import DriftEntry, DriftReport

_SNOOZE_FILE = ".driftwatch_snooze.json"


def _snooze_path(directory: str = ".") -> str:
    return os.path.join(directory, _SNOOZE_FILE)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SnoozeRule:
    resource_id: str
    until: str  # ISO-8601 UTC
    reason: str = ""
    kind: Optional[str] = None
    provider: Optional[str] = None

    def is_expired(self) -> bool:
        try:
            expiry = datetime.fromisoformat(self.until)
        except ValueError:
            return True
        return datetime.now(timezone.utc) >= expiry

    def matches(self, entry: DriftEntry) -> bool:
        if self.is_expired():
            return False
        if entry.resource_id != self.resource_id:
            return False
        if self.kind and entry.kind != self.kind:
            return False
        if self.provider and entry.provider != self.provider:
            return False
        return True


@dataclass
class SnoozeResult:
    snoozed: List[DriftEntry] = field(default_factory=list)
    active: List[DriftEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "snoozed_count": len(self.snoozed),
            "active_count": len(self.active),
            "snoozed": [{"resource_id": e.resource_id, "kind": e.kind} for e in self.snoozed],
        }


def snooze_report(report: DriftReport, rules: List[SnoozeRule]) -> SnoozeResult:
    result = SnoozeResult()
    for entry in report.entries:
        if any(r.matches(entry) for r in rules):
            result.snoozed.append(entry)
        else:
            result.active.append(entry)
    return result


def save_rules(rules: List[SnoozeRule], directory: str = ".") -> None:
    data = [
        {
            "resource_id": r.resource_id,
            "until": r.until,
            "reason": r.reason,
            "kind": r.kind,
            "provider": r.provider,
        }
        for r in rules
    ]
    with open(_snooze_path(directory), "w") as fh:
        json.dump(data, fh, indent=2)


def load_rules(directory: str = ".") -> List[SnoozeRule]:
    path = _snooze_path(directory)
    if not os.path.exists(path):
        return []
    with open(path) as fh:
        data = json.load(fh)
    return [
        SnoozeRule(
            resource_id=d["resource_id"],
            until=d["until"],
            reason=d.get("reason", ""),
            kind=d.get("kind"),
            provider=d.get("provider"),
        )
        for d in data
    ]
