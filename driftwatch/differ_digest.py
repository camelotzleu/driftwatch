"""differ_digest.py — produce a human-readable digest summary of a DriftReport.

A *digest* condenses a DriftReport into a compact, shareable block of text or
structured data that can be embedded in emails, Slack messages, or CI logs
without the full per-attribute detail of the standard reporter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from driftwatch.differ import DriftReport, DriftEntry


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class DigestEntry:
    """One line in the digest — one drift entry condensed to key fields."""

    resource_id: str
    kind: str
    provider: str
    change_type: str          # "added" | "removed" | "changed"
    changed_keys: List[str]   # attribute keys that differ (empty for add/remove)

    def to_dict(self) -> dict:
        return {
            "resource_id": self.resource_id,
            "kind": self.kind,
            "provider": self.provider,
            "change_type": self.change_type,
            "changed_keys": self.changed_keys,
        }


@dataclass
class DigestReport:
    """Full digest of a DriftReport."""

    total: int = 0
    added: int = 0
    removed: int = 0
    changed: int = 0
    providers: List[str] = field(default_factory=list)
    entries: List[DigestEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "added": self.added,
            "removed": self.removed,
            "changed": self.changed,
            "providers": self.providers,
            "entries": [e.to_dict() for e in self.entries],
        }

    def to_text(self) -> str:
        """Return a compact multi-line text digest."""
        lines: List[str] = [
            f"DriftWatch Digest — {self.total} change(s) detected",
            f"  Added: {self.added}  Removed: {self.removed}  Changed: {self.changed}",
            f"  Providers: {', '.join(self.providers) if self.providers else 'none'}",
        ]
        if self.entries:
            lines.append("  Top changes:")
            for e in self.entries[:10]:  # cap at 10 lines for compactness
                keys_str = f" [{', '.join(e.changed_keys)}]" if e.changed_keys else ""
                lines.append(
                    f"    [{e.change_type.upper():7s}] {e.provider}/{e.kind}/{e.resource_id}{keys_str}"
                )
            if len(self.entries) > 10:
                lines.append(f"    … and {len(self.entries) - 10} more")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _change_type(entry: DriftEntry) -> str:
    """Derive a simple change type label from a DriftEntry."""
    if entry.baseline_attributes is None:
        return "added"
    if entry.current_attributes is None:
        return "removed"
    return "changed"


def _changed_keys(entry: DriftEntry) -> List[str]:
    """Return the list of attribute keys that differ between baseline and current."""
    if entry.attribute_diff is None:
        return []
    return list(entry.attribute_diff.keys())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_digest(
    report: DriftReport,
    max_entries: Optional[int] = None,
) -> DigestReport:
    """Build a :class:`DigestReport` from a :class:`DriftReport`.

    Args:
        report: The drift report to digest.
        max_entries: If set, only include this many entries in the digest
            (useful for very large reports).  Counts still reflect the full
            report.

    Returns:
        A populated :class:`DigestReport`.
    """
    digest = DigestReport()
    providers: Dict[str, bool] = {}

    for entry in report.entries:
        ctype = _change_type(entry)
        digest.total += 1
        if ctype == "added":
            digest.added += 1
        elif ctype == "removed":
            digest.removed += 1
        else:
            digest.changed += 1

        providers[entry.provider] = True

        if max_entries is None or len(digest.entries) < max_entries:
            digest.entries.append(
                DigestEntry(
                    resource_id=entry.resource_id,
                    kind=entry.kind,
                    provider=entry.provider,
                    change_type=ctype,
                    changed_keys=_changed_keys(entry),
                )
            )

    digest.providers = sorted(providers.keys())
    return digest
