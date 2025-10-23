"""Performance monitoring and metrics collection.

This module provides decorators and utilities for tracking application performance,
including execution times, cache statistics, and API call counts.

Key features:
    - Performance tracking decorators for sync and async functions
    - Metrics collection and aggregation
    - Cache hit/miss rate tracking
    - JSON-based metrics storage
    - Statistics reporting

Example:
    >>> from app.core.monitoring import track_performance, metrics_collector
    >>> @track_performance("expensive_calculation")
    ... def calculate_something():
    ...     return expensive_operation()
    >>> # Later, get statistics
    >>> stats = metrics_collector.get_statistics()
"""

import functools
import json
import logging
import time
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class MetricsCollector:
    """Collects and aggregates application metrics.

    Tracks performance metrics including execution times, call counts,
    cache statistics, and error counts. Provides methods for retrieving
    statistics and persisting metrics to disk.

    Attributes:
        metrics: Dictionary storing all collected metrics by operation name
        cache_stats: Dictionary tracking cache hit/miss counts
        error_counts: Dictionary tracking error counts by operation

    Example:
        >>> collector = MetricsCollector()
        >>> collector.record_execution("api_call", duration=1.5, success=True)
        >>> stats = collector.get_statistics()
        >>> print(f"Average time: {stats['api_call']['avg_duration']:.3f}s")
    """

    def __init__(self) -> None:
        """Initialize the metrics collector."""
        self.metrics: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.cache_stats: dict[str, int] = {"hits": 0, "misses": 0}
        self.error_counts: dict[str, int] = defaultdict(int)

    def record_execution(
        self, operation_name: str, duration: float, success: bool = True, **metadata: Any
    ) -> None:
        """Record execution metrics for an operation.

        Args:
            operation_name: Name of the operation being tracked
            duration: Execution duration in seconds
            success: Whether the operation completed successfully
            **metadata: Additional metadata to store with the metric

        Example:
            >>> collector.record_execution(
            ...     "load_sheet",
            ...     duration=2.5,
            ...     success=True,
            ...     worksheet="Assets"
            ... )
        """
        entry = {
            "timestamp": time.time(),
            "duration": duration,
            "success": success,
            **metadata,
        }
        self.metrics[operation_name].append(entry)

        if not success:
            self.error_counts[operation_name] += 1

        logger.debug(
            f"Metrics: {operation_name} - {duration:.3f}s - {'✓' if success else '✗'} {metadata}"
        )

    def record_cache_hit(self) -> None:
        """Record a cache hit event.

        Example:
            >>> collector.record_cache_hit()
        """
        self.cache_stats["hits"] += 1

    def record_cache_miss(self) -> None:
        """Record a cache miss event.

        Example:
            >>> collector.record_cache_miss()
        """
        self.cache_stats["misses"] += 1

    def get_statistics(self) -> dict[str, Any]:
        """Get aggregated statistics for all tracked operations.

        Calculates statistics including:
        - Total calls per operation
        - Average, min, max execution times
        - Success/error rates
        - Cache hit rate

        Returns:
            Dictionary containing statistics for each operation and overall cache stats

        Example:
            >>> stats = collector.get_statistics()
            >>> print(f"Cache hit rate: {stats['cache']['hit_rate']:.1%}")
            >>> print(f"API calls: {stats['load_sheet']['total_calls']}")
        """
        stats: dict[str, Any] = {}

        for operation_name, entries in self.metrics.items():
            if not entries:
                continue

            durations = [e["duration"] for e in entries]
            successes = sum(1 for e in entries if e["success"])

            stats[operation_name] = {
                "total_calls": len(entries),
                "successful_calls": successes,
                "failed_calls": len(entries) - successes,
                "avg_duration": sum(durations) / len(durations),
                "min_duration": min(durations),
                "max_duration": max(durations),
                "total_duration": sum(durations),
            }

        # Add cache statistics
        total_cache_ops = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = self.cache_stats["hits"] / total_cache_ops if total_cache_ops > 0 else 0.0

        stats["cache"] = {
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "total_operations": total_cache_ops,
            "hit_rate": hit_rate,
        }

        return stats

    def save_to_file(self, filepath: Path) -> None:
        """Save current metrics to a JSON file.

        Args:
            filepath: Path where metrics JSON should be saved

        Example:
            >>> collector.save_to_file(Path("metrics/app_metrics.json"))
        """
        try:
            stats = self.get_statistics()
            filepath.parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, "w") as f:
                json.dump(stats, f, indent=2)

            logger.info(f"Metrics saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save metrics to {filepath}: {e}")

    def reset(self) -> None:
        """Reset all collected metrics.

        Example:
            >>> collector.reset()  # Start fresh
        """
        self.metrics.clear()
        self.cache_stats = {"hits": 0, "misses": 0}
        self.error_counts.clear()
        logger.info("Metrics reset")


def track_performance(operation_name: str) -> Callable:
    """Decorator to track execution time and success rate of functions.

    Works with both synchronous and asynchronous functions. Automatically
    records execution duration and success/failure status to the global
    metrics collector.

    Args:
        operation_name: Name to identify this operation in metrics

    Returns:
        Decorator function that wraps the target function with performance tracking

    Example:
        >>> @track_performance("calculate_net_worth")
        ... def calculate_net_worth(data):
        ...     return data.sum()
        >>> # Execution time will be automatically logged

        >>> @track_performance("fetch_api_data")
        ... async def fetch_data():
        ...     return await api_call()
        >>> # Works with async functions too

    Note:
        Decorated functions preserve their original name and docstring.
        Exceptions are re-raised after being recorded as failures.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Handle async functions
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> T:
                start = time.perf_counter()
                success = True
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    logger.error(f"Performance tracking: {operation_name} failed with error: {e}")
                    raise
                finally:
                    duration = time.perf_counter() - start
                    metrics_collector.record_execution(operation_name, duration, success)

            return async_wrapper  # type: ignore

        # Handle sync functions
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> T:
                start = time.perf_counter()
                success = True
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    logger.error(f"Performance tracking: {operation_name} failed with error: {e}")
                    raise
                finally:
                    duration = time.perf_counter() - start
                    metrics_collector.record_execution(operation_name, duration, success)

            return sync_wrapper  # type: ignore

    return decorator


# Global metrics collector instance
metrics_collector = MetricsCollector()

# Note: asyncio import needed for iscoroutinefunction check
import asyncio  # noqa: E402
