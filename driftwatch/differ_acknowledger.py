"""Acknowledgement tracking for drift entries.

Allows operators to acknowledge known drift entries so they are flagged
as reviewed rather than surfacing as new findings on every run.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from driftwatch.differ import DriftEntry, DriftReport


def _ack_path(base_dir: str = ".") -> Path:
    return Path(base_dir) / ".driftwatch" / "acknowledged.json"


@dataclass
class AckRule:
    resource_id: str
    kind: Optional[str] = None
    provider: Optional[str] = None
    reason: str = ""

    def matches(self, entry: DriftEntry) -> bool:
        if entry.resource_id != self.resource_id:
            return False
        if self.kind and entry.kind != self.kind:
            return False
        if self.provider and entry.provider != self.provider:
            return False
        return True


@dataclass
class AcknowledgedEntry:
    entry: DriftEntry
    reason: str

    def to_dict(self) -> dict:
        return {
            "resource_id": self.entry.resource_id,
            "kind": self.entry.kind,
            "provider": self.entry.provider,
            "change_type": self.entry.change_type,
            "reason": self.reason,
        }


@dataclass
class AckReport:
    acknowledged: List[AcknowledgedEntry] = field(default_factory=list)
    unacknowledged: List[DriftEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "acknowledged": [a.to_dict() for a in self.acknowledged],
            "unacknowledged": [
                {
                    "resource_id": e.resource_id,
                    "kind": e.kind,
                    "provider": e.provider,
                    "change_type": e.change_type,
                }
                for e in self.unacknowledged
            ],
            "total": len(self.acknowledged) + len(self.unacknowledged),
            "acknowledged_count": len(self.acknowledged),
            "unacknowledged_count": len(self.unacknowledged),
        }


def load_ack_rules(base_dir: str = ".") -> List[AckRule]:
    path = _ack_path(base_dir)
    if not path.exists():
        return []
    with path.open() as fh:
        raw = json.load(fh)
    return [
        AckRule(
            resource_id=r["resource_id"],
            kind=r.get("kind"),
            provider=r.get("provider"),
            reason=r.get("reason", ""),
        )
        for r in raw
    ]


def save_ack_rules(rules: List[AckRule], base_dir: str = ".") -> None:
    path = _ack_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(
            [
                {
                    "resource_id": r.resource_id,
                    "kind": r.kind,
                    "provider": r.provider,
                    "reason": r.reason,
                }
                for r in rules
            ],
            fh,
            indent=2,
        )


def acknowledge_report(report: DriftReport, rules: List[AckRule]) -> AckReport:
    result = AckReport()
    for entry in report.entries:
        matched = next((r for r in rules if r.matches(entry)), None)
        if matched:
            result.acknowledged.append(AcknowledgedEntry(entry=entry, reason=matched.reason))
        else:
            result.unacknowledged.append(entry)
    return result
