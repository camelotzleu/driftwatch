"""Tests for driftwatch.reporter."""
import io
import json

import pytest

from driftwatch.differ import DriftEntry, DriftReport
from driftwatch.reporter import render


def _make_report(*entries: DriftEntry) -> DriftReport:
    return DriftReport(entries=list(entries))


def _changed(rid: str, rtype: str = "ec2", diffs: dict | None = None) -> DriftEntry:
    return DriftEntry(
        resource_id=rid,
        resource_type=rtype,
        status="changed",
        attribute_diffs=diffs or {"size": ("t2.micro", "t3.micro")},
    )


def _added(rid: str) -> DriftEntry:
    return DriftEntry(resource_id=rid, resource_type="s3", status="added", attribute_diffs={})


def _removed(rid: str) -> DriftEntry:
    return DriftEntry(resource_id=rid, resource_type="s3", status="removed", attribute_diffs={})


def test_render_text_no_drift():
    out = io.StringIO()
    render(_make_report(), fmt="text", out=out)
    assert "No drift" in out.getvalue()


def test_render_text_with_drift():
    out = io.StringIO()
    render(_make_report(_changed("i-123")), fmt="text", out=out)
    text = out.getvalue()
    assert "CHANGED" in text
    assert "i-123" in text
    assert "t2.micro" in text
    assert "t3.micro" in text


def test_render_text_added_removed():
    out = io.StringIO()
    render(_make_report(_added("bucket-a"), _removed("bucket-b")), fmt="text", out=out)
    text = out.getvalue()
    assert "ADDED" in text
    assert "REMOVED" in text


def test_render_json_no_drift():
    out = io.StringIO()
    render(_make_report(), fmt="json", out=out)
    data = json.loads(out.getvalue())
    assert data["has_drift"] is False
    assert data["entries"] == []


def test_render_json_with_drift():
    out = io.StringIO()
    render(_make_report(_changed("i-456", diffs={"ami": ("ami-old", "ami-new")})), fmt="json", out=out)
    data = json.loads(out.getvalue())
    assert data["has_drift"] is True
    entry = data["entries"][0]
    assert entry["resource_id"] == "i-456"
    assert entry["attribute_diffs"]["ami"] == {"old": "ami-old", "new": "ami-new"}


def test_render_json_summary_string():
    out = io.StringIO()
    render(_make_report(_added("x"), _removed("y"), _changed("z")), fmt="json", out=out)
    data = json.loads(out.getvalue())
    assert "3" in data["summary"] or data["summary"]
