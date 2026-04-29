"""Round-trip drift report serialization and deserialization utilities."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from driftwatch.differ import DriftEntry, DriftReport


@dataclass
class RoundTripResult:
    ok: bool
    original_count: int
    restored_count: int
    mismatches: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "original_count": self.original_count,
            "restored_count": self.restored_count,
            "mismatches": self.mismatches,
        }


def _entry_to_dict(entry: DriftEntry) -> dict[str, Any]:
    return {
        "resource_id": entry.resource_id,
        "kind": entry.kind,
        "provider": entry.provider,
        "change_type": entry.change_type,
        "attribute_diff": entry.attribute_diff,
    }


def _entry_from_dict(data: dict[str, Any]) -> DriftEntry:
    return DriftEntry(
        resource_id=data["resource_id"],
        kind=data["kind"],
        provider=data["provider"],
        change_type=data["change_type"],
        attribute_diff=data.get("attribute_diff", {}),
    )


def report_to_dict(report: DriftReport) -> dict[str, Any]:
    """Serialize a DriftReport to a plain dictionary."""
    return {
        "provider": report.provider,
        "entries": [_entry_to_dict(e) for e in report.entries],
    }


def report_from_dict(data: dict[str, Any]) -> DriftReport:
    """Deserialize a DriftReport from a plain dictionary."""
    entries = [_entry_from_dict(e) for e in data.get("entries", [])]
    report = DriftReport(provider=data.get("provider", "unknown"))
    for entry in entries:
        report.entries.append(entry)
    return report


def verify_round_trip(report: DriftReport) -> RoundTripResult:
    """Serialize then deserialize a report and verify fidelity."""
    serialized = report_to_dict(report)
    restored = report_from_dict(serialized)

    mismatches: list[str] = []
    original_ids = {e.resource_id: e for e in report.entries}
    restored_ids = {e.resource_id: e for e in restored.entries}

    for rid, orig in original_ids.items():
        if rid not in restored_ids:
            mismatches.append(f"missing after restore: {rid}")
            continue
        rest = restored_ids[rid]
        if orig.change_type != rest.change_type:
            mismatches.append(f"{rid}: change_type {orig.change_type!r} != {rest.change_type!r}")
        if orig.attribute_diff != rest.attribute_diff:
            mismatches.append(f"{rid}: attribute_diff mismatch")

    for rid in restored_ids:
        if rid not in original_ids:
            mismatches.append(f"extra after restore: {rid}")

    return RoundTripResult(
        ok=len(mismatches) == 0,
        original_count=len(report.entries),
        restored_count=len(restored.entries),
        mismatches=mismatches,
    )
