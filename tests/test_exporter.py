"""Tests for driftwatch.exporter."""
import csv
import io
import json
from datetime import datetime, timezone

import pytest

from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.exporter import export, to_csv, to_json


def _make_report() -> DriftReport:
    entries = [
        DriftEntry(
            status="changed",
            resource_id="i-001",
            resource_type="ec2_instance",
            provider="aws",
            attribute_diff={"instance_type": {"baseline": "t2.micro", "current": "t3.small"}},
        ),
        DriftEntry(
            status="added",
            resource_id="i-002",
            resource_type="ec2_instance",
            provider="aws",
            attribute_diff=None,
        ),
        DriftEntry(
            status="removed",
            resource_id="i-003",
            resource_type="ec2_instance",
            provider="aws",
            attribute_diff=None,
        ),
    ]
    return DriftReport(
        provider="aws",
        generated_at=datetime(2024, 1, 1, tzinfo=timezone.utc).isoformat(),
        entries=entries,
    )


def test_to_json_structure():
    report = _make_report()
    result = json.loads(to_json(report))
    assert result["provider"] == "aws"
    assert result["has_drift"] is True
    assert len(result["entries"]) == 3
    assert result["entries"][0]["status"] == "changed"


def test_to_json_attribute_diff_present():
    report = _make_report()
    result = json.loads(to_json(report))
    diff = result["entries"][0]["attribute_diff"]
    assert diff["instance_type"]["baseline"] == "t2.micro"
    assert diff["instance_type"]["current"] == "t3.small"


def test_to_csv_headers():
    report = _make_report()
    reader = csv.DictReader(io.StringIO(to_csv(report)))
    assert set(reader.fieldnames) == {"status", "resource_id", "resource_type", "provider", "changes"}


def test_to_csv_row_count():
    report = _make_report()
    reader = list(csv.DictReader(io.StringIO(to_csv(report))))
    assert len(reader) == 3


def test_to_csv_changes_column():
    report = _make_report()
    rows = list(csv.DictReader(io.StringIO(to_csv(report))))
    assert "t2.micro" in rows[0]["changes"]
    assert "t3.small" in rows[0]["changes"]


def test_export_json():
    report = _make_report()
    result = export(report, "json")
    assert json.loads(result)["provider"] == "aws"


def test_export_csv():
    report = _make_report()
    result = export(report, "csv")
    assert "resource_id" in result


def test_export_invalid_format():
    report = _make_report()
    with pytest.raises(ValueError, match="Unsupported export format"):
        export(report, "xml")
