"""Intelligent state and cache manager for financial data.

This module provides a sophisticated caching system optimized for monthly financial
data that doesn't change frequently. It uses data hashing to auto-invalidate cache
when source data changes and runs expensive computations in thread pools to avoid
blocking the UI.

Key features:
    - Hash-based cache invalidation
    - TTL-based expiration (default 24 hours)
    - Thread pool execution for heavy computations
    - Cache statistics and debugging tools

Example:
    >>> from app.core.state_manager import state_manager
    >>> # Cache expensive calculation
    >>> result = await state_manager.get_or_compute(
    ...     'assets_sheet',
    ...     'net_worth_calc',
    ...     lambda: expensive_pandas_operation()
    ... )
"""

import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

from nicegui import app

from app.core.monitoring import metrics_collector

logger = logging.getLogger(__name__)
T = TypeVar("T")


class StateManager:
    """Intelligent state and cache manager for financial data.

    Optimized for monthly data updates with long TTL caching to minimize
    expensive pandas calculations. Automatically invalidates cache when
    source data changes by hashing user storage data.

    Attributes:
        default_ttl: Default cache time-to-live in seconds (24 hours)

    Example:
        >>> state_manager = StateManager(default_ttl_seconds=86400)
        >>> result = await state_manager.get_or_compute(
        ...     'assets_sheet',
        ...     'calculation_key',
        ...     lambda: heavy_computation()
        ... )
    """

    def __init__(self, default_ttl_seconds: int = 86400) -> None:
        """Initialize the state manager.

        Args:
            default_ttl_seconds: Default cache TTL in seconds. Default is 86400 (24 hours),
                                suitable for monthly financial data updates
        """
        self.default_ttl = default_ttl_seconds
        self._cache: dict[str, dict[str, Any]] = {}

    def _get_cache_key(self, user_storage_key: str, computation_key: str) -> str:
        """Generate unique cache key for user data + computation.

        Uses hash of general storage data to automatically invalidate cache when
        source data changes.

        Args:
            user_storage_key: Key in app.storage.general (e.g., 'assets_sheet')
            computation_key: Unique identifier for this computation

        Returns:
            Cache key string combining storage key, computation key, and data hash

        Note:
            Falls back to a simpler key format if storage access fails.
        """
        # Use data hash to invalidate cache when data changes
        try:
            user_data = app.storage.general.get(user_storage_key, "")
            data_str = str(user_data) if user_data is not None else ""
            data_hash = hash(data_str)
            return f"{user_storage_key}:{computation_key}:{data_hash}"
        except Exception as e:
            # Fallback if there are storage issues
            logger.warning(f"Failed to generate cache key with hash, using fallback: {e}")
            return f"{user_storage_key}:{computation_key}:fallback"

    def _is_cache_valid(self, cache_entry: dict[str, Any]) -> bool:
        """Check if cache entry is still valid based on TTL.

        Args:
            cache_entry: Cache entry dictionary with 'timestamp' and 'ttl' keys

        Returns:
            True if cache entry is still within its TTL, False otherwise
        """
        if "timestamp" not in cache_entry or "ttl" not in cache_entry:
            return False
        return time.time() - cache_entry["timestamp"] < cache_entry["ttl"]

    async def get_or_compute(
        self,
        user_storage_key: str,
        computation_key: str,
        compute_fn: Callable[[], T],
        ttl_seconds: int | None = None,
    ) -> T:
        """Get cached result or compute if not available/expired.

        First checks cache for a valid entry. If not found or expired, runs the
        computation function in a thread pool to avoid blocking the UI, then
        caches the result.

        Args:
            user_storage_key: Key in app.storage.general (e.g., 'assets_sheet')
            computation_key: Unique identifier for this computation (e.g., 'net_worth_calc')
            compute_fn: Callable that computes the value (should be thread-safe)
            ttl_seconds: Cache time-to-live in seconds. If None, uses default TTL (24h)

        Returns:
            Computed or cached value of type T

        Example:
            >>> def expensive_calculation():
            ...     return df['Net Worth'].sum()  # Heavy pandas operation
            >>> result = await state_manager.get_or_compute(
            ...     'assets_sheet',
            ...     'total_net_worth',
            ...     expensive_calculation,
            ...     ttl_seconds=3600
            ... )
        """
        cache_key = self._get_cache_key(user_storage_key, computation_key)
        ttl = ttl_seconds or self.default_ttl

        # Check cache first
        if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]):
            logger.debug(f"Cache hit for {computation_key}")
            metrics_collector.record_cache_hit()
            return self._cache[cache_key]["value"]

        # Compute new value - run in thread pool to avoid blocking UI
        logger.debug(f"Cache miss for {computation_key}, computing value")
        metrics_collector.record_cache_miss()
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, compute_fn)
        except Exception as e:
            # Direct fallback if there are thread pool issues (pickling errors, etc.)
            logger.error(
                f"Thread pool execution failed for {computation_key}, falling back to direct execution: {e}"
            )
            result = compute_fn()

        # Cache the result
        self._cache[cache_key] = {"value": result, "timestamp": time.time(), "ttl": ttl}

        return result

    def invalidate_cache(self, pattern: str | None = None) -> None:
        """Invalidate cache entries matching a pattern or clear all cache.

        Args:
            pattern: Optional pattern string. If provided, only invalidates cache keys
                    containing this pattern. If None, clears entire cache.

        Example:
            >>> # Clear all cache
            >>> state_manager.invalidate_cache()
            >>> # Clear only assets_sheet related cache
            >>> state_manager.invalidate_cache('assets_sheet')
        """
        if pattern is None:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cache cleared: {count} entries invalidated")
        else:
            keys_to_remove = [key for key in self._cache.keys() if pattern in key]
            for key in keys_to_remove:
                del self._cache[key]
            logger.info(
                f"Cache partially cleared: {len(keys_to_remove)} entries matching '{pattern}' invalidated"
            )

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics for debugging and monitoring.

        Returns:
            Dictionary containing:
            - total_entries: Total number of cache entries
            - valid_entries: Number of entries still within TTL
            - expired_entries: Number of expired entries
            - cache_keys: List of all cache keys

        Example:
            >>> stats = state_manager.get_cache_stats()
            >>> print(f"Cache hit rate: {stats['valid_entries'] / stats['total_entries']}")
        """
        total_entries = len(self._cache)
        valid_entries = sum(1 for entry in self._cache.values() if self._is_cache_valid(entry))

        return {
            "total_entries": total_entries,
            "valid_entries": valid_entries,
            "expired_entries": total_entries - valid_entries,
            "cache_keys": list(self._cache.keys()),
        }


# Cache decorator for synchronous functions
def cached_computation(user_storage_key: str, computation_key: str, ttl_seconds: int | None = None):
    """Decorator to automatically cache results of heavy computations.

    Wraps a synchronous function to automatically cache its results using the
    global state_manager. The decorated function becomes async.

    Args:
        user_storage_key: Key in app.storage.general for cache invalidation
        computation_key: Unique identifier for this computation
        ttl_seconds: Optional cache TTL in seconds

    Returns:
        Decorator function that converts sync function to cached async function

    Example:
        >>> @cached_computation('assets_sheet', 'net_worth_calculation', ttl_seconds=3600)
        ... def calculate_net_worth():
        ...     return df['Net Worth'].sum()  # Heavy pandas operation
        >>> # Function is now async and cached
        >>> result = await calculate_net_worth()

    Note:
        The decorated function becomes async and must be awaited when called.
    """

    def decorator(func):
        async def async_wrapper():
            return await state_manager.get_or_compute(
                user_storage_key, computation_key, func, ttl_seconds
            )

        # Preserve original function metadata
        async_wrapper.__name__ = func.__name__
        async_wrapper.__doc__ = func.__doc__
        return async_wrapper

    return decorator


# Global state manager instance
state_manager = StateManager()
