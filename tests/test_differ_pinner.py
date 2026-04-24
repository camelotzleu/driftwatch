"""Tests for driftwatch.differ_pinner."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.differ_pinner import (
    PinnedEntry,
    _entry_is_pinned,
    load_pins,
    pin_report,
    save_pins,
)


def _entry(
    resource_id: str = "r1",
    kind: str = "instance",
    provider: str = "aws",
    change_type: str = "changed",
) -> DriftEntry:
    return DriftEntry(
        resource_id=resource_id,
        kind=kind,
        provider=provider,
        change_type=change_type,
        attribute_diff={},
    )


def _report(*entries: DriftEntry) -> DriftReport:
    r = DriftReport()
    for e in entries:
        r.entries.append(e)
    return r


# ---------------------------------------------------------------------------
# PinnedEntry serialisation
# ---------------------------------------------------------------------------

def test_pinned_entry_round_trip():
    pe = PinnedEntry(resource_id="r1", kind="bucket", provider="gcp", reason="ok")
    assert PinnedEntry.from_dict(pe.to_dict()) == pe


def test_pinned_entry_defaults():
    pe = PinnedEntry.from_dict({"resource_id": "x", "kind": "vm", "provider": "azure"})
    assert pe.reason == ""


# ---------------------------------------------------------------------------
# _entry_is_pinned
# ---------------------------------------------------------------------------

def test_entry_is_pinned_match():
    pins = [PinnedEntry(resource_id="r1", kind="instance", provider="aws")]
    assert _entry_is_pinned(_entry("r1"), pins) is True


def test_entry_is_pinned_no_match_different_id():
    pins = [PinnedEntry(resource_id="r2", kind="instance", provider="aws")]
    assert _entry_is_pinned(_entry("r1"), pins) is False


def test_entry_is_pinned_empty_pins():
    assert _entry_is_pinned(_entry(), []) is False


# ---------------------------------------------------------------------------
# pin_report
# ---------------------------------------------------------------------------

def test_pin_report_all_unpinned():
    report = _report(_entry("r1"), _entry("r2"))
    result = pin_report(report, [])
    assert len(result.unpinned) == 2
    assert len(result.pinned) == 0


def test_pin_report_partial():
    pins = [PinnedEntry(resource_id="r1", kind="instance", provider="aws")]
    report = _report(_entry("r1"), _entry("r2"))
    result = pin_report(report, pins)
    assert len(result.pinned) == 1
    assert result.pinned[0].resource_id == "r1"
    assert len(result.unpinned) == 1
    assert result.unpinned[0].resource_id == "r2"


def test_pin_report_to_dict_structure():
    pins = [PinnedEntry(resource_id="r1", kind="instance", provider="aws")]
    report = _report(_entry("r1"), _entry("r2"))
    d = pin_report(report, pins).to_dict()
    assert d["pinned_count"] == 1
    assert d["unpinned_count"] == 1
    assert d["unpinned"][0]["resource_id"] == "r2"


# ---------------------------------------------------------------------------
# save / load pins
# ---------------------------------------------------------------------------

def test_save_and_load_pins(tmp_path):
    pins = [
        PinnedEntry(resource_id="r1", kind="instance", provider="aws", reason="ack"),
        PinnedEntry(resource_id="r2", kind="bucket", provider="gcp"),
    ]
    save_pins(pins, base_dir=str(tmp_path))
    loaded = load_pins(base_dir=str(tmp_path))
    assert loaded == pins


def test_load_pins_missing_file(tmp_path):
    result = load_pins(base_dir=str(tmp_path))
    assert result == []


def test_save_pins_creates_directory(tmp_path):
    pins = [PinnedEntry(resource_id="x", kind="vm", provider="azure")]
    save_pins(pins, base_dir=str(tmp_path))
    assert (tmp_path / ".driftwatch" / "pinned.json").exists()
