"""Configuration loading and validation for driftwatch."""

import os
from dataclasses import dataclass, field
from typing import List, Optional

import yaml


@dataclass
class ProviderConfig:
    name: str
    region: str
    profile: Optional[str] = None


@dataclass
class DriftWatchConfig:
    providers: List[ProviderConfig] = field(default_factory=list)
    output_format: str = "table"
    ignore_keys: List[str] = field(default_factory=list)
    baseline_path: str = "baseline.json"

    @classmethod
    def from_dict(cls, data: dict) -> "DriftWatchConfig":
        providers = [
            ProviderConfig(
                name=p["name"],
                region=p["region"],
                profile=p.get("profile"),
            )
            for p in data.get("providers", [])
        ]
        return cls(
            providers=providers,
            output_format=data.get("output_format", "table"),
            ignore_keys=data.get("ignore_keys", []),
            baseline_path=data.get("baseline_path", "baseline.json"),
        )

    @classmethod
    def load(cls, path: Optional[str] = None) -> "DriftWatchConfig":
        candidates = [path, "driftwatch.yaml", "driftwatch.yml", ".driftwatch.yaml"]
        for candidate in candidates:
            if candidate and os.path.isfile(candidate):
                with open(candidate, "r") as f:
                    data = yaml.safe_load(f) or {}
                return cls.from_dict(data)
        return cls()
