from __future__ import annotations

from driftwatch.config import ProviderConfig
from driftwatch.collectors.base import BaseCollector


def get_collector(config: ProviderConfig) -> BaseCollector:
    """Return the appropriate collector for the given provider config."""
    provider = config.provider.lower()

    if provider == "mock":
        from driftwatch.collectors.mock_collector import MockCollector
        return MockCollector(config)

    if provider == "aws":
        from driftwatch.collectors.aws_collector import AWSCollector
        return AWSCollector(config)

    if provider == "gcp":
        from driftwatch.collectors.gcp_collector import GCPCollector
        return GCPCollector(config)

    if provider == "azure":
        from driftwatch.collectors.azure_collector import AzureCollector
        return AzureCollector(config)

    raise ValueError(f"Unknown provider: {config.provider!r}")
