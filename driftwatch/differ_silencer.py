"""Silencer: temporarily mute drift entries matching a rule until an expiry time."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from driftwatch.differ import DriftEntry, DriftReport


@dataclass
class SilenceRule:
    resource_id: Optional[str] = None
    kind: Optional[str] = None
    provider: Optional[str] = None
    until: Optional[str] = None  # ISO-8601 datetime string
    reason: str = ""

    def is_expired(self) -> bool:
        if not self.until:
            return False
        expiry = datetime.fromisoformat(self.until)
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > expiry

    def matches(self, entry: DriftEntry) -> bool:
        if self.is_expired():
            return False
        if self.resource_id and entry.resource_id != self.resource_id:
            return False
        if self.kind and entry.kind != self.kind:
            return False
        if self.provider and entry.provider != self.provider:
            return False
        return True


@dataclass
class SilenceResult:
    active: List[DriftEntry] = field(default_factory=list)
    silenced: List[DriftEntry] = field(default_factory=list)
    rules_applied: int = 0

    def to_dict(self) -> dict:
        return {
            "active_count": len(self.active),
            "silenced_count": len(self.silenced),
            "rules_applied": self.rules_applied,
            "silenced": [
                {"resource_id": e.resource_id, "kind": e.kind, "provider": e.provider}
                for e in self.silenced
            ],
        }


def silence_report(report: DriftReport, rules: List[SilenceRule]) -> SilenceResult:
    """Filter drift entries that match any active silence rule."""
    active_rules = [r for r in rules if not r.is_expired()]
    result = SilenceResult(rules_applied=len(active_rules))
    for entry in report.entries:
        if any(r.matches(entry) for r in active_rules):
            result.silenced.append(entry)
        else:
            result.active.append(entry)
    return result


def rules_from_list(raw: List[dict]) -> List[SilenceRule]:
    return [
        SilenceRule(
            resource_id=r.get("resource_id"),
            kind=r.get("kind"),
            provider=r.get("provider"),
            until=r.get("until"),
            reason=r.get("reason", ""),
        )
        for r in raw
    ]
