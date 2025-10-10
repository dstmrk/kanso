"""
Tests for state_manager module.

Tests StateManager cache logic.
"""

import pytest
import time
from unittest.mock import Mock, patch

from app.core.state_manager import StateManager


class TestStateManager:
    """Tests for StateManager class."""

    @pytest.fixture
    def manager(self):
        """Create StateManager instance with short TTL for testing."""
        return StateManager(default_ttl_seconds=1)

    @pytest.mark.asyncio
    async def test_cache_miss_and_compute(self, manager):
        """Test cache miss triggers computation."""
        compute_fn = Mock(return_value=42)

        # Mock the entire storage.user object
        mock_user_storage = Mock()
        mock_user_storage.get.return_value = 'test_data'

        with patch('app.core.state_manager.app.storage') as mock_storage:
            mock_storage.user = mock_user_storage
            result = await manager.get_or_compute('data', 'test_key', compute_fn)

        assert result == 42
        compute_fn.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_hit(self, manager):
        """Test cache hit returns cached value without computation."""
        compute_fn = Mock(return_value=42)

        # Mock the entire storage.user object
        mock_user_storage = Mock()
        mock_user_storage.get.return_value = 'test_data'

        with patch('app.core.state_manager.app.storage') as mock_storage:
            mock_storage.user = mock_user_storage
            # First call - cache miss
            result1 = await manager.get_or_compute('data', 'test_key', compute_fn)
            # Second call - cache hit
            result2 = await manager.get_or_compute('data', 'test_key', compute_fn)

        assert result1 == 42
        assert result2 == 42
        # Compute function should only be called once
        compute_fn.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_expiration(self, manager):
        """Test cache expires after TTL."""
        call_count = [0]

        def compute_fn():
            call_count[0] += 1
            return call_count[0]

        # Mock the entire storage.user object
        mock_user_storage = Mock()
        mock_user_storage.get.return_value = 'test_data'

        with patch('app.core.state_manager.app.storage') as mock_storage:
            mock_storage.user = mock_user_storage
            # First call
            result1 = await manager.get_or_compute('data', 'test_key', compute_fn, ttl_seconds=1)
            assert result1 == 1

            # Wait for cache to expire
            time.sleep(1.1)

            # Second call - cache should be expired
            result2 = await manager.get_or_compute('data', 'test_key', compute_fn, ttl_seconds=1)
            assert result2 == 2

    @pytest.mark.asyncio
    async def test_cache_invalidation_by_data_change(self, manager):
        """Test cache is invalidated when data changes."""
        compute_fn = Mock(return_value=42)

        # First call with original data
        mock_user_storage1 = Mock()
        mock_user_storage1.get.return_value = 'test_data_1'

        with patch('app.core.state_manager.app.storage') as mock_storage:
            mock_storage.user = mock_user_storage1
            result1 = await manager.get_or_compute('data', 'test_key', compute_fn)

        # Second call with changed data
        mock_user_storage2 = Mock()
        mock_user_storage2.get.return_value = 'test_data_2'

        with patch('app.core.state_manager.app.storage') as mock_storage:
            mock_storage.user = mock_user_storage2
            result2 = await manager.get_or_compute('data', 'test_key', compute_fn)

        assert result1 == 42
        assert result2 == 42
        # Compute function should be called twice (data changed)
        assert compute_fn.call_count == 2

    def test_invalidate_all_cache(self, manager):
        """Test invalidating all cache entries."""
        manager._cache['key1'] = {'value': 1, 'timestamp': time.time(), 'ttl': 100}
        manager._cache['key2'] = {'value': 2, 'timestamp': time.time(), 'ttl': 100}

        manager.invalidate_cache()

        assert len(manager._cache) == 0

    def test_invalidate_cache_by_pattern(self, manager):
        """Test invalidating cache entries by pattern."""
        manager._cache['data:key1:hash'] = {'value': 1, 'timestamp': time.time(), 'ttl': 100}
        manager._cache['data:key2:hash'] = {'value': 2, 'timestamp': time.time(), 'ttl': 100}
        manager._cache['other:key3:hash'] = {'value': 3, 'timestamp': time.time(), 'ttl': 100}

        manager.invalidate_cache(pattern='data')

        # Only 'other:key3:hash' should remain
        assert len(manager._cache) == 1
        assert 'other:key3:hash' in manager._cache

    def test_get_cache_stats(self, manager):
        """Test getting cache statistics."""
        current_time = time.time()

        # Add valid entry
        manager._cache['valid'] = {'value': 1, 'timestamp': current_time, 'ttl': 100}
        # Add expired entry
        manager._cache['expired'] = {'value': 2, 'timestamp': current_time - 200, 'ttl': 100}

        stats = manager.get_cache_stats()

        assert stats['total_entries'] == 2
        assert stats['valid_entries'] == 1
        assert stats['expired_entries'] == 1
        assert 'valid' in stats['cache_keys']
        assert 'expired' in stats['cache_keys']

    def test_cache_key_generation_with_fallback(self, manager):
        """Test cache key generation with fallback on error."""
        # Mock storage to raise exception when accessing .get()
        mock_user_storage = Mock()
        mock_user_storage.get.side_effect = Exception("Storage error")

        with patch('app.core.state_manager.app.storage') as mock_storage:
            mock_storage.user = mock_user_storage
            key = manager._get_cache_key('test_storage', 'test_computation')

        # Should return fallback key
        assert 'fallback' in key
        assert 'test_storage' in key
        assert 'test_computation' in key

    def test_is_cache_valid(self, manager):
        """Test cache validity check."""
        current_time = time.time()

        # Valid entry
        valid_entry = {'timestamp': current_time, 'ttl': 100}
        assert manager._is_cache_valid(valid_entry) is True

        # Expired entry
        expired_entry = {'timestamp': current_time - 200, 'ttl': 100}
        assert manager._is_cache_valid(expired_entry) is False

        # Missing timestamp
        invalid_entry = {'ttl': 100}
        assert manager._is_cache_valid(invalid_entry) is False

        # Missing ttl
        invalid_entry2 = {'timestamp': current_time}
        assert manager._is_cache_valid(invalid_entry2) is False
