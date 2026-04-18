"""Tests for driftwatch configuration loading."""

import os
import textwrap
import pytest

from driftwatch.config import DriftWatchConfig, ProviderConfig


YAML_CONTENT = textwrap.dedent("""
    providers:
      - name: aws
        region: us-east-1
        profile: dev
      - name: gcp
        region: us-central1
    output_format: json
    ignore_keys:
      - tags
      - last_modified
    baseline_path: snapshots/baseline.json
""")


def test_from_dict_full():
    data = {
        "providers": [{"name": "aws", "region": "eu-west-1"}],
        "output_format": "json",
        "ignore_keys": ["tags"],
        "baseline_path": "my_baseline.json",
    }
    cfg = DriftWatchConfig.from_dict(data)
    assert len(cfg.providers) == 1
    assert cfg.providers[0].name == "aws"
    assert cfg.output_format == "json"
    assert "tags" in cfg.ignore_keys
    assert cfg.baseline_path == "my_baseline.json"


def test_from_dict_defaults():
    cfg = DriftWatchConfig.from_dict({})
    assert cfg.providers == []
    assert cfg.output_format == "table"
    assert cfg.ignore_keys == []
    assert cfg.baseline_path == "baseline.json"


def test_load_from_file(tmp_path):
    config_file = tmp_path / "driftwatch.yaml"
    config_file.write_text(YAML_CONTENT)
    cfg = DriftWatchConfig.load(str(config_file))
    assert len(cfg.providers) == 2
    assert cfg.providers[0].profile == "dev"
    assert cfg.providers[1].profile is None
    assert cfg.output_format == "json"
    assert cfg.baseline_path == "snapshots/baseline.json"


def test_load_returns_defaults_when_no_file():
    cfg = DriftWatchConfig.load("/nonexistent/path.yaml")
    assert isinstance(cfg, DriftWatchConfig)
    assert cfg.providers == []


def test_provider_config_fields():
    p = ProviderConfig(name="azure", region="eastus", profile="prod")
    assert p.name == "azure"
    assert p.region == "eastus"
    assert p.profile == "prod"
