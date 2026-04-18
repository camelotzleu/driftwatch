"""Scheduler: run drift checks on a recurring interval and emit reports."""
import time
import logging
from typing import Callable, Optional

from driftwatch.config import DriftWatchConfig
from driftwatch.collectors import get_collector
from driftwatch.baseline import load as load_baseline, save as save_baseline
from driftwatch.differ import compare
from driftwatch.reporter import render

logger = logging.getLogger(__name__)


def _run_once(cfg: DriftWatchConfig, fmt: str, on_drift: Optional[Callable] = None) -> bool:
    """Collect, diff against baseline, render. Returns True if drift detected."""
    collector = get_collector(cfg.provider)
    current = collector.collect()
    baseline = load_baseline(cfg.provider.name)
    if baseline is None:
        logger.info("No baseline found; saving current snapshot as baseline.")
        save_baseline(cfg.provider.name, current)
        return False
    report = compare(baseline, current)
    output = render(report, fmt)
    print(output)
    if report.has_drift() and on_drift:
        on_drift(report)
    return report.has_drift()


def run_scheduler(
    cfg: DriftWatchConfig,
    interval: int = 300,
    fmt: str = "text",
    on_drift: Optional[Callable] = None,
    max_iterations: Optional[int] = None,
) -> None:
    """Run drift checks every *interval* seconds."""
    iteration = 0
    logger.info("Scheduler started (interval=%ds)", interval)
    while True:
        try:
            _run_once(cfg, fmt, on_drift=on_drift)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Error during drift check: %s", exc)
        iteration += 1
        if max_iterations is not None and iteration >= max_iterations:
            break
        time.sleep(interval)
