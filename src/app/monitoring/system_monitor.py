"""
System monitoring module for EmbedIQ backend.

This module provides functionality to monitor system resources such as
CPU, memory, disk space, and network statistics.
"""

import os
import psutil
import logging
import time
from typing import Dict, Any, List, Optional
import shutil
from datetime import datetime

logger = logging.getLogger(__name__)


class SystemMonitor:
    """
    Monitor system resources and provide metrics.
    """

    def __init__(self, data_dir: str = None):
        """
        Initialize the system monitor.

        Args:
            data_dir: The data directory to monitor for disk usage
        """
        self.data_dir = data_dir
        self.start_time = datetime.now()
        logger.info("SystemMonitor initialized")

    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get current system metrics.

        Returns:
            Dictionary containing system metrics
        """
        try:
            # Get CPU metrics
            cpu_metrics = self._get_cpu_metrics()

            # Get memory metrics
            memory_metrics = self._get_memory_metrics()

            # Get disk metrics
            disk_metrics = self._get_disk_metrics()

            # Get network metrics
            network_metrics = self._get_network_metrics()

            # Get process metrics
            process_metrics = self._get_process_metrics()

            # Combine all metrics
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
                "cpu": cpu_metrics,
                "memory": memory_metrics,
                "disk": disk_metrics,
                "network": network_metrics,
                "process": process_metrics,
            }

            return metrics
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _get_cpu_metrics(self) -> Dict[str, Any]:
        """
        Get CPU metrics.

        Returns:
            Dictionary containing CPU metrics
        """
        return {
            "percent": psutil.cpu_percent(interval=0.1),
            "count": psutil.cpu_count(),
            "physical_count": psutil.cpu_count(logical=False),
            "load_avg": os.getloadavg(),
            "per_cpu": psutil.cpu_percent(interval=0.1, percpu=True),
        }

    def _get_memory_metrics(self) -> Dict[str, Any]:
        """
        Get memory metrics.

        Returns:
            Dictionary containing memory metrics
        """
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "percent": memory.percent,
            "swap_total": swap.total,
            "swap_used": swap.used,
            "swap_percent": swap.percent,
        }

    def _get_disk_metrics(self) -> Dict[str, Any]:
        """
        Get disk metrics.

        Returns:
            Dictionary containing disk metrics
        """
        # Get overall disk usage
        disk_usage = psutil.disk_usage("/")

        # Get data directory usage if specified
        data_dir_usage = None
        if self.data_dir and os.path.exists(self.data_dir):
            data_dir_usage = shutil.disk_usage(self.data_dir)

        metrics = {
            "total": disk_usage.total,
            "used": disk_usage.used,
            "free": disk_usage.free,
            "percent": disk_usage.percent,
        }

        # Add data directory metrics if available
        if data_dir_usage:
            metrics["data_dir"] = {
                "path": self.data_dir,
                "total": data_dir_usage.total,
                "used": data_dir_usage.used,
                "free": data_dir_usage.free,
                "percent": (data_dir_usage.used / data_dir_usage.total) * 100,
            }

            # Get user directory sizes if data_dir exists
            user_dirs = {}
            try:
                for user_dir in os.listdir(self.data_dir):
                    user_path = os.path.join(self.data_dir, user_dir)
                    if os.path.isdir(user_path):
                        user_dirs[user_dir] = self._get_dir_size(user_path)
                
                if user_dirs:
                    metrics["data_dir"]["user_directories"] = user_dirs
            except Exception as e:
                logger.warning(f"Error getting user directory sizes: {e}")

        return metrics

    def _get_network_metrics(self) -> Dict[str, Any]:
        """
        Get network metrics.

        Returns:
            Dictionary containing network metrics
        """
        net_io = psutil.net_io_counters()

        return {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
            "errin": net_io.errin,
            "errout": net_io.errout,
            "dropin": net_io.dropin,
            "dropout": net_io.dropout,
        }

    def _get_process_metrics(self) -> Dict[str, Any]:
        """
        Get process metrics for the current process.

        Returns:
            Dictionary containing process metrics
        """
        process = psutil.Process()
        
        return {
            "pid": process.pid,
            "cpu_percent": process.cpu_percent(interval=0.1),
            "memory_percent": process.memory_percent(),
            "memory_info": {
                "rss": process.memory_info().rss,
                "vms": process.memory_info().vms,
            },
            "threads": len(process.threads()),
            "open_files": len(process.open_files()),
            "connections": len(process.connections()),
        }

    def _get_dir_size(self, path: str) -> int:
        """
        Get the size of a directory in bytes.

        Args:
            path: The directory path

        Returns:
            Directory size in bytes
        """
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total_size += os.path.getsize(fp)
        return total_size

    def get_health_check(self) -> Dict[str, Any]:
        """
        Get a comprehensive health check.

        Returns:
            Dictionary containing health check results
        """
        try:
            # Get basic metrics
            metrics = self.get_system_metrics()
            
            # Determine health status based on thresholds
            cpu_healthy = metrics["cpu"]["percent"] < 90
            memory_healthy = metrics["memory"]["percent"] < 90
            disk_healthy = metrics["disk"]["percent"] < 90
            
            # Overall health status
            is_healthy = cpu_healthy and memory_healthy and disk_healthy
            
            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "checks": {
                    "cpu": {
                        "status": "healthy" if cpu_healthy else "warning",
                        "percent": metrics["cpu"]["percent"],
                    },
                    "memory": {
                        "status": "healthy" if memory_healthy else "warning",
                        "percent": metrics["memory"]["percent"],
                    },
                    "disk": {
                        "status": "healthy" if disk_healthy else "warning",
                        "percent": metrics["disk"]["percent"],
                    },
                },
                "metrics": metrics,
            }
        except Exception as e:
            logger.error(f"Error performing health check: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
