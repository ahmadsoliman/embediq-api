"""
LightRAG monitoring module for EmbedIQ backend.

This module provides functionality to monitor LightRAG performance metrics
such as query latency, throughput, and resource consumption.
"""

import logging
import time
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from collections import deque
import threading
import statistics
from functools import wraps

logger = logging.getLogger(__name__)


class LightRAGMonitor:
    """
    Monitor LightRAG performance metrics.
    """

    def __init__(self, max_history: int = 100):
        """
        Initialize the LightRAG monitor.

        Args:
            max_history: Maximum number of historical metrics to keep
        """
        self.max_history = max_history
        self.query_times = deque(maxlen=max_history)
        self.search_times = deque(maxlen=max_history)
        self.insert_times = deque(maxlen=max_history)
        self.operation_counts = {
            "query": 0,
            "search": 0,
            "insert": 0,
            "errors": 0,
        }
        self.start_time = datetime.now()
        self._lock = threading.RLock()
        logger.info("LightRAGMonitor initialized")

    def record_query_time(self, elapsed_time: float) -> None:
        """
        Record a query operation time.

        Args:
            elapsed_time: Time taken for the query operation in seconds
        """
        with self._lock:
            self.query_times.append(elapsed_time)
            self.operation_counts["query"] += 1

    def record_search_time(self, elapsed_time: float) -> None:
        """
        Record a search operation time.

        Args:
            elapsed_time: Time taken for the search operation in seconds
        """
        with self._lock:
            self.search_times.append(elapsed_time)
            self.operation_counts["search"] += 1

    def record_insert_time(self, elapsed_time: float) -> None:
        """
        Record an insert operation time.

        Args:
            elapsed_time: Time taken for the insert operation in seconds
        """
        with self._lock:
            self.insert_times.append(elapsed_time)
            self.operation_counts["insert"] += 1

    def record_error(self) -> None:
        """
        Record an error in LightRAG operations.
        """
        with self._lock:
            self.operation_counts["errors"] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current LightRAG performance metrics.

        Returns:
            Dictionary containing LightRAG performance metrics
        """
        with self._lock:
            # Calculate query metrics
            query_metrics = self._calculate_operation_metrics(self.query_times)

            # Calculate search metrics
            search_metrics = self._calculate_operation_metrics(self.search_times)

            # Calculate insert metrics
            insert_metrics = self._calculate_operation_metrics(self.insert_times)

            # Calculate throughput
            uptime_seconds = (datetime.now() - self.start_time).total_seconds()
            total_operations = (
                sum(self.operation_counts.values()) - self.operation_counts["errors"]
            )

            throughput = 0
            if uptime_seconds > 0:
                throughput = total_operations / uptime_seconds

            # Combine all metrics
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": uptime_seconds,
                "operations": dict(self.operation_counts),
                "throughput": throughput,
                "query": query_metrics,
                "search": search_metrics,
                "insert": insert_metrics,
            }

            return metrics

    def _calculate_operation_metrics(self, times: deque) -> Dict[str, Any]:
        """
        Calculate metrics for an operation.

        Args:
            times: Deque of operation times

        Returns:
            Dictionary containing operation metrics
        """
        if not times:
            return {
                "count": 0,
                "avg_time": 0,
                "min_time": 0,
                "max_time": 0,
                "p95_time": 0,
                "p99_time": 0,
            }

        times_list = list(times)
        times_list.sort()

        p95_index = int(len(times_list) * 0.95)
        p99_index = int(len(times_list) * 0.99)

        return {
            "count": len(times_list),
            "avg_time": statistics.mean(times_list),
            "min_time": min(times_list),
            "max_time": max(times_list),
            "p95_time": times_list[p95_index - 1] if p95_index > 0 else times_list[-1],
            "p99_time": times_list[p99_index - 1] if p99_index > 0 else times_list[-1],
        }

    def reset_metrics(self) -> None:
        """
        Reset all metrics.
        """
        with self._lock:
            self.query_times.clear()
            self.search_times.clear()
            self.insert_times.clear()
            self.operation_counts = {
                "query": 0,
                "search": 0,
                "insert": 0,
                "errors": 0,
            }
            self.start_time = datetime.now()
            logger.info("LightRAG metrics reset")


# Create a singleton instance
_monitor = None


def get_lightrag_monitor() -> LightRAGMonitor:
    """
    Get or create the LightRAG monitor singleton.

    Returns:
        The LightRAG monitor singleton
    """
    global _monitor
    if _monitor is None:
        _monitor = LightRAGMonitor()
    return _monitor


def monitor_lightrag_operation(operation_type: str):
    """
    Decorator to monitor LightRAG operations.

    Args:
        operation_type: Type of operation ('query', 'search', 'insert')

    Returns:
        Decorated function
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            monitor = get_lightrag_monitor()
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                elapsed_time = time.time() - start_time

                if operation_type == "query":
                    monitor.record_query_time(elapsed_time)
                elif operation_type == "search":
                    monitor.record_search_time(elapsed_time)
                elif operation_type == "insert":
                    monitor.record_insert_time(elapsed_time)

                return result
            except Exception as e:
                monitor.record_error()
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            monitor = get_lightrag_monitor()
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed_time = time.time() - start_time

                if operation_type == "query":
                    monitor.record_query_time(elapsed_time)
                elif operation_type == "search":
                    monitor.record_search_time(elapsed_time)
                elif operation_type == "insert":
                    monitor.record_insert_time(elapsed_time)

                return result
            except Exception as e:
                monitor.record_error()
                raise

        # Return the appropriate wrapper based on whether the function is async or not
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
