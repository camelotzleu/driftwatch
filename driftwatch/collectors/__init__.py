from driftwatch.collectors.base import BaseCollector
from driftwatch.collectors.mock_collector import MockCollector

COLLECTOR_REGISTRY: dict[str, type[BaseCollector]] = {
    "mock": MockCollector,
}


def get_collector(provider_name: str, provider_config) -> BaseCollector:
    """Instantiate and return a collector for the given provider name."""
    cls = COLLECTOR_REGISTRY.get(provider_name)
    if cls is None:
        raise ValueError(
            f"Unknown provider '{provider_name}'. "
            f"Available: {list(COLLECTOR_REGISTRY.keys())}"
        )
    return cls(provider_config)


__all__ = ["BaseCollector", "MockCollector", "get_collector", "COLLECTOR_REGISTRY"]
