"""AWS collector — fetches EC2 instance snapshots via boto3."""
from __future__ import annotations

from typing import Any, Dict, List

from driftwatch.collectors.base import BaseCollector
from driftwatch.snapshot import Snapshot

try:
    import boto3
except ImportError:  # pragma: no cover
    boto3 = None  # type: ignore


class AWSCollector(BaseCollector):
    """Collect EC2 instance state from AWS."""

    @property
    def provider_name(self) -> str:
        return "aws"

    def collect(self) -> Snapshot:
        if boto3 is None:
            raise RuntimeError("boto3 is required for the AWS collector. Install it with: pip install boto3")

        session = boto3.Session(
            region_name=self.config.region or "us-east-1",
            profile_name=self.config.profile or None,
        )
        ec2 = session.client("ec2")
        snapshot = self._make_snapshot()

        paginator = ec2.get_paginator("describe_instances")
        for page in paginator.paginate():
            for reservation in page.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    resource_id = instance["InstanceId"]
                    attributes = self._extract_attributes(instance)
                    snapshot.add(resource_id, "ec2_instance", attributes)

        return snapshot

    # ------------------------------------------------------------------
    def _extract_attributes(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        tags = {t["Key"]: t["Value"] for t in instance.get("Tags", [])}
        return {
            "instance_type": instance.get("InstanceType"),
            "state": instance.get("State", {}).get("Name"),
            "ami_id": instance.get("ImageId"),
            "key_name": instance.get("KeyName"),
            "subnet_id": instance.get("SubnetId"),
            "vpc_id": instance.get("VpcId"),
            "private_ip": instance.get("PrivateIpAddress"),
            "public_ip": instance.get("PublicIpAddress"),
            "tags": tags,
        }
