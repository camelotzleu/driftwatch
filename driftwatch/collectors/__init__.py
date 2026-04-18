"""Collector registry — maps provider names to collector classes."""
from __future__ import annotations

from driftwatch.config import ProviderConfig
from driftwatch.collectors.base import BaseCollector
from driftwatch.collectors.mock_collector import MockCollector

_REGISTRY: dict[str, type[BaseCollector]] = {
    "mock": MockCollector,
}

# Register AWS collector only when boto3 is available
try:
    from driftwatch.collectors.aws_collector import AWSCollector
    _REGISTRY["aws"] = AWSCollector
except ImportError:
    pass


def get_collector(config: ProviderConfig) -> BaseCollector:
    """Return an instantiated collector for the given provider config."""
    cls = _REGISTRY.get(config.provider)
    if cls is None:
        raise ValueError(
            f"Unknown provider '{config.provider}'. "
            f"Available: {sorted(_REGISTRY)}"
        )
    return cls(config)
