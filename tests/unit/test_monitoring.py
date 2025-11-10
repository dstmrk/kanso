"""Tests for monitoring module."""

import json
import time
from pathlib import Path

import pytest

from app.core.monitoring import MetricsCollector, track_performance


class TestMetricsCollector:
    """Tests for MetricsCollector class."""

    @pytest.fixture
    def collector(self):
        """Create a fresh MetricsCollector instance for each test."""
        return MetricsCollector()

    def test_record_execution_success(self, collector):
        """Should record successful execution."""
        collector.record_execution("test_op", 0.123, success=True)

        assert "test_op" in collector.metrics
        assert len(collector.metrics["test_op"]) == 1
        assert collector.metrics["test_op"][0]["duration"] == 0.123
        assert collector.metrics["test_op"][0]["success"] is True

    def test_record_execution_failure(self, collector):
        """Should record failed execution and increment error count."""
        collector.record_execution("test_op", 0.456, success=False)

        assert "test_op" in collector.metrics
        assert collector.metrics["test_op"][0]["success"] is False
        assert collector.error_counts["test_op"] == 1

    def test_record_execution_with_metadata(self, collector):
        """Should record execution with custom metadata."""
        metadata = {"user": "test", "action": "load"}
        collector.record_execution("test_op", 0.1, success=True, **metadata)

        entry = collector.metrics["test_op"][0]
        assert entry["user"] == "test"
        assert entry["action"] == "load"

    def test_record_cache_hit(self, collector):
        """Should increment cache hits."""
        collector.record_cache_hit()
        collector.record_cache_hit()

        assert collector.cache_stats["hits"] == 2
        assert collector.cache_stats["misses"] == 0

    def test_record_cache_miss(self, collector):
        """Should increment cache misses."""
        collector.record_cache_miss()
        collector.record_cache_miss()
        collector.record_cache_miss()

        assert collector.cache_stats["hits"] == 0
        assert collector.cache_stats["misses"] == 3

    def test_get_statistics_with_data(self, collector):
        """Should calculate statistics correctly."""
        # Record some operations
        collector.record_execution("op1", 0.1, success=True)
        collector.record_execution("op1", 0.2, success=True)
        collector.record_execution("op1", 0.3, success=False)
        collector.record_cache_hit()
        collector.record_cache_miss()

        stats = collector.get_statistics()

        # Check operation stats
        assert "op1" in stats
        assert stats["op1"]["total_calls"] == 3
        assert stats["op1"]["successful_calls"] == 2
        assert stats["op1"]["failed_calls"] == 1
        assert stats["op1"]["avg_duration"] == pytest.approx(0.2)
        assert stats["op1"]["min_duration"] == 0.1
        assert stats["op1"]["max_duration"] == 0.3
        assert stats["op1"]["total_duration"] == pytest.approx(0.6)

        # Check cache stats
        assert "cache" in stats
        assert stats["cache"]["hits"] == 1
        assert stats["cache"]["misses"] == 1
        assert stats["cache"]["total_operations"] == 2
        assert stats["cache"]["hit_rate"] == 0.5

    def test_get_statistics_empty(self, collector):
        """Should return empty stats when no data collected."""
        stats = collector.get_statistics()

        assert "cache" in stats
        assert stats["cache"]["hits"] == 0
        assert stats["cache"]["misses"] == 0
        assert stats["cache"]["total_operations"] == 0
        assert stats["cache"]["hit_rate"] == 0.0

    def test_get_statistics_cache_hit_rate_calculation(self, collector):
        """Should calculate cache hit rate correctly."""
        collector.record_cache_hit()
        collector.record_cache_hit()
        collector.record_cache_hit()
        collector.record_cache_miss()

        stats = collector.get_statistics()

        assert stats["cache"]["hit_rate"] == 0.75

    def test_save_to_file(self, collector, tmp_path):
        """Should save statistics to JSON file."""
        collector.record_execution("test_op", 0.123, success=True)
        collector.record_cache_hit()

        filepath = tmp_path / "metrics" / "test_metrics.json"
        collector.save_to_file(filepath)

        # Check file was created
        assert filepath.exists()

        # Check content
        with open(filepath) as f:
            data = json.load(f)

        assert "test_op" in data
        assert "cache" in data
        assert data["cache"]["hits"] == 1

    def test_save_to_file_creates_parent_dirs(self, collector, tmp_path):
        """Should create parent directories if they don't exist."""
        filepath = tmp_path / "deep" / "nested" / "path" / "metrics.json"
        collector.save_to_file(filepath)

        assert filepath.exists()
        assert filepath.parent.exists()

    def test_reset(self, collector):
        """Should reset all metrics."""
        # Add some data
        collector.record_execution("test_op", 0.1, success=True)
        collector.record_cache_hit()
        collector.record_cache_miss()

        # Reset
        collector.reset()

        # Check everything is cleared
        assert len(collector.metrics) == 0
        assert collector.cache_stats["hits"] == 0
        assert collector.cache_stats["misses"] == 0
        assert len(collector.error_counts) == 0


class TestTrackPerformanceDecorator:
    """Tests for track_performance decorator."""

    def test_track_sync_function_success(self):
        """Should track synchronous function execution."""
        collector = MetricsCollector()

        @track_performance("sync_test")
        def sync_func(x):
            return x * 2

        # Replace global collector temporarily
        import app.core.monitoring
        original_collector = app.core.monitoring.metrics_collector
        app.core.monitoring.metrics_collector = collector

        try:
            result = sync_func(5)

            assert result == 10
            assert "sync_test" in collector.metrics
            assert len(collector.metrics["sync_test"]) == 1
            assert collector.metrics["sync_test"][0]["success"] is True
        finally:
            app.core.monitoring.metrics_collector = original_collector

    def test_track_sync_function_failure(self):
        """Should track synchronous function failures."""
        collector = MetricsCollector()

        @track_performance("sync_fail")
        def failing_func():
            raise ValueError("Test error")

        # Replace global collector temporarily
        import app.core.monitoring
        original_collector = app.core.monitoring.metrics_collector
        app.core.monitoring.metrics_collector = collector

        try:
            with pytest.raises(ValueError):
                failing_func()

            assert "sync_fail" in collector.metrics
            assert collector.metrics["sync_fail"][0]["success"] is False
        finally:
            app.core.monitoring.metrics_collector = original_collector

    @pytest.mark.asyncio
    async def test_track_async_function_success(self):
        """Should track asynchronous function execution."""
        collector = MetricsCollector()

        @track_performance("async_test")
        async def async_func(x):
            await asyncio.sleep(0.01)
            return x * 3

        # Replace global collector temporarily
        import app.core.monitoring
        original_collector = app.core.monitoring.metrics_collector
        app.core.monitoring.metrics_collector = collector

        try:
            result = await async_func(4)

            assert result == 12
            assert "async_test" in collector.metrics
            assert len(collector.metrics["async_test"]) == 1
            assert collector.metrics["async_test"][0]["success"] is True
            # Duration should be > 0.01 (sleep time)
            assert collector.metrics["async_test"][0]["duration"] >= 0.01
        finally:
            app.core.monitoring.metrics_collector = original_collector

    @pytest.mark.asyncio
    async def test_track_async_function_failure(self):
        """Should track asynchronous function failures."""
        collector = MetricsCollector()

        @track_performance("async_fail")
        async def failing_async_func():
            raise RuntimeError("Async error")

        # Replace global collector temporarily
        import app.core.monitoring
        original_collector = app.core.monitoring.metrics_collector
        app.core.monitoring.metrics_collector = collector

        try:
            with pytest.raises(RuntimeError):
                await failing_async_func()

            assert "async_fail" in collector.metrics
            assert collector.metrics["async_fail"][0]["success"] is False
        finally:
            app.core.monitoring.metrics_collector = original_collector


# Import asyncio for async tests
import asyncio  # noqa: E402
