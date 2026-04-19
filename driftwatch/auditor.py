"""Audit log: records every drift detection run with metadata."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from driftwatch.differ import DriftReport


def audit_path(config_dir: str = ".driftwatch") -> Path:
    return Path(config_dir) / "audit.jsonl"


@dataclass
class AuditEntry:
    timestamp: str
    provider: str
    total_resources: int
    added: int
    removed: int
    changed: int
    has_drift: bool
    triggered_alerts: List[str] = field(default_factory=list)
    note: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "provider": self.provider,
            "total_resources": self.total_resources,
            "added": self.added,
            "removed": self.removed,
            "changed": self.changed,
            "has_drift": self.has_drift,
            "triggered_alerts": self.triggered_alerts,
            "note": self.note,
        }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def record(report: DriftReport, provider: str, triggered_alerts: Optional[List[str]] = None,
           note: Optional[str] = None, config_dir: str = ".driftwatch") -> AuditEntry:
    entry = AuditEntry(
        timestamp=_now_iso(),
        provider=provider,
        total_resources=len(report.added) + len(report.removed) + len(report.changed),
        added=len(report.added),
        removed=len(report.removed),
        changed=len(report.changed),
        has_drift=report.has_drift(),
        triggered_alerts=triggered_alerts or [],
        note=note,
    )
    path = audit_path(config_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as fh:
        fh.write(json.dumps(entry.to_dict()) + "\n")
    return entry


def load(config_dir: str = ".driftwatch") -> List[AuditEntry]:
    path = audit_path(config_dir)
    if not path.exists():
        return []
    entries = []
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                d = json.loads(line)
                entries.append(AuditEntry(**d))
    return entries


def clear(config_dir: str = ".driftwatch") -> None:
    audit_path(config_dir).unlink(missing_ok=True)
