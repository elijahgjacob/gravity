"""Timing utilities for latency tracking."""

import time
from contextlib import contextmanager
from typing import Generator

from src.core.logging_config import get_logger

logger = get_logger(__name__)


@contextmanager
def timer(operation: str) -> Generator[None, None, None]:
    """
    Context manager for timing operations.
    
    Args:
        operation: Description of the operation being timed
    
    Yields:
        None
    
    Example:
        with timer("database query"):
            result = db.query()
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
        logger.debug(f"{operation} completed in {elapsed:.2f}ms")


class LatencyTracker:
    """Track latency for different components of the pipeline."""
    
    def __init__(self):
        self.timings = {}
        self.start_time = None
    
    def start(self):
        """Start tracking total latency."""
        self.start_time = time.perf_counter()
    
    def record(self, component: str, duration_ms: float):
        """
        Record latency for a component.
        
        Args:
            component: Name of the component
            duration_ms: Duration in milliseconds
        """
        self.timings[component] = duration_ms
    
    def get_total(self) -> float:
        """
        Get total elapsed time since start.
        
        Returns:
            Total time in milliseconds
        """
        if self.start_time is None:
            return 0.0
        return (time.perf_counter() - self.start_time) * 1000
    
    def get_breakdown(self) -> dict:
        """
        Get breakdown of timings by component.
        
        Returns:
            Dictionary of component timings
        """
        return {
            "total_ms": self.get_total(),
            "components": self.timings.copy()
        }
