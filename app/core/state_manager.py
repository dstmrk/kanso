import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

from nicegui import app

logger = logging.getLogger(__name__)
T = TypeVar("T")


class StateManager:
    """
    Intelligent state and cache manager for financial data.

    Optimized for monthly data updates - uses long TTL caching
    to minimize expensive pandas calculations.
    """

    def __init__(self, default_ttl_seconds: int = 86400) -> None:  # 24 hours default
        self.default_ttl = default_ttl_seconds
        self._cache: dict[str, dict[str, Any]] = {}

    def _get_cache_key(self, user_storage_key: str, computation_key: str) -> str:
        """Generate unique cache key for user data + computation."""
        # Use data hash to invalidate cache when data changes
        try:
            user_data = app.storage.user.get(user_storage_key, "")
            data_str = str(user_data) if user_data is not None else ""
            data_hash = hash(data_str)
            return f"{user_storage_key}:{computation_key}:{data_hash}"
        except Exception as e:
            # Fallback if there are storage issues
            logger.warning(f"Failed to generate cache key with hash, using fallback: {e}")
            return f"{user_storage_key}:{computation_key}:fallback"

    def _is_cache_valid(self, cache_entry: dict[str, Any]) -> bool:
        """Check if cache entry is still valid."""
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
        """
        Get cached result or compute if not available/expired.

        Args:
            user_storage_key: Key in app.storage.user (e.g., 'data_sheet')
            computation_key: Unique identifier for this computation
            compute_fn: Function to compute the value
            ttl_seconds: Cache time-to-live (defaults to 24h for monthly data)
        """
        cache_key = self._get_cache_key(user_storage_key, computation_key)
        ttl = ttl_seconds or self.default_ttl

        # Check cache first
        if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]):
            logger.debug(f"Cache hit for {computation_key}")
            return self._cache[cache_key]["value"]

        # Compute new value - run in thread pool to avoid blocking UI
        logger.debug(f"Cache miss for {computation_key}, computing value")
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, compute_fn)
        except Exception as e:
            # Direct fallback if there are thread pool issues
            logger.warning(
                f"Thread pool execution failed for {computation_key}, using direct execution: {e}"
            )
            result = compute_fn()

        # Cache the result
        self._cache[cache_key] = {"value": result, "timestamp": time.time(), "ttl": ttl}

        return result

    def invalidate_cache(self, pattern: str | None = None) -> None:
        """
        Invalidate cache entries.

        Args:
            pattern: If provided, only invalidate keys containing this pattern
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
        """Get cache statistics for debugging."""
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
    """
    Decorator to automatically cache results of heavy computations.

    Usage:
        @cached_computation('data_sheet', 'net_worth_calculation')
        def expensive_calculation():
            return heavy_pandas_work()
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
