"""
Unit tests for monitoring module.
"""

import pytest
import time
import asyncio
import os
import psutil
from unittest.mock import patch, MagicMock

from app.monitoring.system_monitor import SystemMonitor
from app.monitoring.lightrag_monitor import (
    LightRAGMonitor,
    get_lightrag_monitor,
    monitor_lightrag_operation,
)


class TestSystemMonitor:
    """Tests for SystemMonitor class"""

    def test_init(self):
        """Test initialization"""
        monitor = SystemMonitor(data_dir="/tmp")
        assert monitor.data_dir == "/tmp"
        assert monitor.start_time is not None

    def test_get_system_metrics(self):
        """Test get_system_metrics method"""
        monitor = SystemMonitor()
        metrics = monitor.get_system_metrics()

        # Check that metrics contains expected keys
        assert "timestamp" in metrics
        assert "uptime_seconds" in metrics
        assert "cpu" in metrics
        assert "memory" in metrics
        assert "disk" in metrics
        assert "network" in metrics
        assert "process" in metrics

        # Check CPU metrics
        assert "percent" in metrics["cpu"]
        assert "count" in metrics["cpu"]
        assert "physical_count" in metrics["cpu"]
        assert "load_avg" in metrics["cpu"]
        assert "per_cpu" in metrics["cpu"]

        # Check memory metrics
        assert "total" in metrics["memory"]
        assert "available" in metrics["memory"]
        assert "used" in metrics["memory"]
        assert "percent" in metrics["memory"]

        # Check disk metrics
        assert "total" in metrics["disk"]
        assert "used" in metrics["disk"]
        assert "free" in metrics["disk"]
        assert "percent" in metrics["disk"]

        # Check network metrics
        assert "bytes_sent" in metrics["network"]
        assert "bytes_recv" in metrics["network"]
        assert "packets_sent" in metrics["network"]
        assert "packets_recv" in metrics["network"]

        # Check process metrics
        assert "pid" in metrics["process"]
        assert "cpu_percent" in metrics["process"]
        assert "memory_percent" in metrics["process"]
        assert "memory_info" in metrics["process"]

    def test_get_health_check(self):
        """Test get_health_check method"""
        monitor = SystemMonitor()
        health = monitor.get_health_check()

        # Check that health contains expected keys
        assert "status" in health
        assert "timestamp" in health
        assert "checks" in health
        assert "metrics" in health

        # Check status
        assert health["status"] in ["healthy", "unhealthy"]

        # Check checks
        assert "cpu" in health["checks"]
        assert "memory" in health["checks"]
        assert "disk" in health["checks"]

        # Check that each check has a status
        assert "status" in health["checks"]["cpu"]
        assert "status" in health["checks"]["memory"]
        assert "status" in health["checks"]["disk"]


class TestLightRAGMonitor:
    """Tests for LightRAGMonitor class"""

    def test_init(self):
        """Test initialization"""
        monitor = LightRAGMonitor(max_history=50)
        assert monitor.max_history == 50
        assert len(monitor.query_times) == 0
        assert len(monitor.search_times) == 0
        assert len(monitor.insert_times) == 0
        assert monitor.operation_counts["query"] == 0
        assert monitor.operation_counts["search"] == 0
        assert monitor.operation_counts["insert"] == 0
        assert monitor.operation_counts["errors"] == 0
        assert monitor.start_time is not None

    def test_record_operations(self):
        """Test recording operations"""
        monitor = LightRAGMonitor()

        # Record operations
        monitor.record_query_time(0.1)
        monitor.record_search_time(0.2)
        monitor.record_insert_time(0.3)
        monitor.record_error()

        # Check that operations were recorded
        assert len(monitor.query_times) == 1
        assert len(monitor.search_times) == 1
        assert len(monitor.insert_times) == 1
        assert monitor.operation_counts["query"] == 1
        assert monitor.operation_counts["search"] == 1
        assert monitor.operation_counts["insert"] == 1
        assert monitor.operation_counts["errors"] == 1

        # Check that times were recorded correctly
        assert monitor.query_times[0] == 0.1
        assert monitor.search_times[0] == 0.2
        assert monitor.insert_times[0] == 0.3

    def test_get_metrics(self):
        """Test get_metrics method"""
        monitor = LightRAGMonitor()

        # Record some operations
        monitor.record_query_time(0.1)
        monitor.record_query_time(0.2)
        monitor.record_search_time(0.3)
        monitor.record_insert_time(0.4)

        # Get metrics
        metrics = monitor.get_metrics()

        # Check that metrics contains expected keys
        assert "timestamp" in metrics
        assert "uptime_seconds" in metrics
        assert "operations" in metrics
        assert "throughput" in metrics
        assert "query" in metrics
        assert "search" in metrics
        assert "insert" in metrics

        # Check operations
        assert metrics["operations"]["query"] == 2
        assert metrics["operations"]["search"] == 1
        assert metrics["operations"]["insert"] == 1

        # Check query metrics
        assert metrics["query"]["count"] == 2
        assert (
            abs(metrics["query"]["avg_time"] - 0.15) < 0.0001
        )  # Use approximate comparison for floating point
        assert metrics["query"]["min_time"] == 0.1
        assert metrics["query"]["max_time"] == 0.2

        # Check search metrics
        assert metrics["search"]["count"] == 1
        assert metrics["search"]["avg_time"] == 0.3

        # Check insert metrics
        assert metrics["insert"]["count"] == 1
        assert metrics["insert"]["avg_time"] == 0.4

    def test_reset_metrics(self):
        """Test reset_metrics method"""
        monitor = LightRAGMonitor()

        # Record some operations
        monitor.record_query_time(0.1)
        monitor.record_search_time(0.2)
        monitor.record_insert_time(0.3)

        # Reset metrics
        monitor.reset_metrics()

        # Check that metrics were reset
        assert len(monitor.query_times) == 0
        assert len(monitor.search_times) == 0
        assert len(monitor.insert_times) == 0
        assert monitor.operation_counts["query"] == 0
        assert monitor.operation_counts["search"] == 0
        assert monitor.operation_counts["insert"] == 0
        assert monitor.operation_counts["errors"] == 0

    def test_get_lightrag_monitor_singleton(self):
        """Test get_lightrag_monitor function"""
        # Get monitor
        monitor1 = get_lightrag_monitor()

        # Get monitor again
        monitor2 = get_lightrag_monitor()

        # Check that both references point to the same object
        assert monitor1 is monitor2

    @pytest.mark.asyncio
    async def test_monitor_lightrag_operation_decorator_async(self):
        """Test monitor_lightrag_operation decorator with async function"""
        # Create a mock monitor
        mock_monitor = MagicMock()

        # Create a decorated async function
        @monitor_lightrag_operation("query")
        async def mock_async_function():
            await asyncio.sleep(0.1)
            return "result"

        # Patch get_lightrag_monitor to return our mock
        with patch(
            "app.monitoring.lightrag_monitor.get_lightrag_monitor",
            return_value=mock_monitor,
        ):
            # Call the decorated function
            result = await mock_async_function()

            # Check that the function returned the expected result
            assert result == "result"

            # Check that record_query_time was called
            assert mock_monitor.record_query_time.called

    def test_monitor_lightrag_operation_decorator_sync(self):
        """Test monitor_lightrag_operation decorator with sync function"""
        # Create a mock monitor
        mock_monitor = MagicMock()

        # Create a decorated sync function
        @monitor_lightrag_operation("search")
        def mock_sync_function():
            time.sleep(0.1)
            return "result"

        # Patch get_lightrag_monitor to return our mock
        with patch(
            "app.monitoring.lightrag_monitor.get_lightrag_monitor",
            return_value=mock_monitor,
        ):
            # Call the decorated function
            result = mock_sync_function()

            # Check that the function returned the expected result
            assert result == "result"

            # Check that record_search_time was called
            assert mock_monitor.record_search_time.called
