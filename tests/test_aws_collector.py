"""Unit tests for AWSCollector using a mocked boto3 client."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from driftwatch.config import ProviderConfig
from driftwatch.collectors.aws_collector import AWSCollector
from driftwatch.snapshot import Snapshot


def _make_config(**kwargs) -> ProviderConfig:
    defaults = {"provider": "aws", "region": "eu-west-1", "profile": None, "enabled": True}
    defaults.update(kwargs)
    return ProviderConfig(**defaults)


def _fake_instance(instance_id: str, itype: str = "t3.micro", state: str = "running") -> dict:
    return {
        "InstanceId": instance_id,
        "InstanceType": itype,
        "State": {"Name": state},
        "ImageId": "ami-abc123",
        "KeyName": "my-key",
        "SubnetId": "subnet-1",
        "VpcId": "vpc-1",
        "PrivateIpAddress": "10.0.0.1",
        "PublicIpAddress": None,
        "Tags": [{"Key": "Name", "Value": "web-server"}],
    }


@patch("driftwatch.collectors.aws_collector.boto3")
def test_collect_returns_snapshot(mock_boto3):
    page = {"Reservations": [{"Instances": [_fake_instance("i-111"), _fake_instance("i-222")]}]}
    paginator = MagicMock()
    paginator.paginate.return_value = [page]
    client = MagicMock()
    client.get_paginator.return_value = paginator
    mock_boto3.Session.return_value.client.return_value = client

    collector = AWSCollector(_make_config())
    snapshot = collector.collect()

    assert isinstance(snapshot, Snapshot)
    assert snapshot.provider == "aws"
    d = snapshot.to_dict()
    ids = [r["resource_id"] for r in d["resources"]]
    assert "i-111" in ids
    assert "i-222" in ids


@patch("driftwatch.collectors.aws_collector.boto3")
def test_collect_extracts_attributes(mock_boto3):
    page = {"Reservations": [{"Instances": [_fake_instance("i-333", itype="m5.large", state="stopped")]}]}
    paginator = MagicMock()
    paginator.paginate.return_value = [page]
    client = MagicMock()
    client.get_paginator.return_value = paginator
    mock_boto3.Session.return_value.client.return_value = client

    snapshot = AWSCollector(_make_config()).collect()
    resources = snapshot.to_dict()["resources"]
    assert len(resources) == 1
    attrs = resources[0]["attributes"]
    assert attrs["instance_type"] == "m5.large"
    assert attrs["state"] == "stopped"
    assert attrs["tags"] == {"Name": "web-server"}


@patch("driftwatch.collectors.aws_collector.boto3")
def test_collect_empty_account(mock_boto3):
    paginator = MagicMock()
    paginator.paginate.return_value = [{"Reservations": []}]
    client = MagicMock()
    client.get_paginator.return_value = paginator
    mock_boto3.Session.return_value.client.return_value = client

    snapshot = AWSCollector(_make_config()).collect()
    assert snapshot.to_dict()["resources"] == []


@patch("driftwatch.collectors.aws_collector.boto3", None)
def test_collect_raises_when_boto3_missing():
    collector = AWSCollector(_make_config())
    with pytest.raises(RuntimeError, match="boto3"):
        collector.collect()


def test_provider_name():
    assert AWSCollector(_make_config()).provider_name == "aws"
