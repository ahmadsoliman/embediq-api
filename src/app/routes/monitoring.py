"""
Monitoring API endpoints for EmbedIQ backend.

This module provides API endpoints for monitoring system resources,
LightRAG performance, and application health.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, Optional
from app.config.app_config import DATA_DIR
from app.monitoring.system_monitor import SystemMonitor
from app.monitoring.lightrag_monitor import get_lightrag_monitor
from app.middleware.auth import validate_token, admin_required

logger = logging.getLogger(__name__)

# Create router
monitoring_router = APIRouter(
    prefix="/monitoring",
    tags=["monitoring"],
)

# Create system monitor
system_monitor = SystemMonitor(data_dir=DATA_DIR)


@monitoring_router.get("/system")
async def get_system_metrics(
    current_user: str = Depends(admin_required),
) -> Dict[str, Any]:
    """
    Get system metrics.

    This endpoint requires admin privileges.

    Returns:
        Dictionary containing system metrics
    """
    logger.info(f"Getting system metrics for admin user: {current_user}")
    return system_monitor.get_system_metrics()


@monitoring_router.get("/lightrag")
async def get_lightrag_metrics(
    current_user: str = Depends(admin_required),
) -> Dict[str, Any]:
    """
    Get LightRAG performance metrics.

    This endpoint requires admin privileges.

    Returns:
        Dictionary containing LightRAG performance metrics
    """
    logger.info(f"Getting LightRAG metrics for admin user: {current_user}")
    monitor = get_lightrag_monitor()
    return monitor.get_metrics()


@monitoring_router.post("/lightrag/reset")
async def reset_lightrag_metrics(
    current_user: str = Depends(admin_required),
) -> Dict[str, Any]:
    """
    Reset LightRAG performance metrics.

    This endpoint requires admin privileges.

    Returns:
        Success message
    """
    logger.info(f"Resetting LightRAG metrics for admin user: {current_user}")
    monitor = get_lightrag_monitor()
    monitor.reset_metrics()
    return {"message": "LightRAG metrics reset successfully"}


@monitoring_router.get("/health")
async def get_health_check() -> Dict[str, Any]:
    """
    Get a comprehensive health check.

    This endpoint is public and used for health monitoring.

    Returns:
        Dictionary containing health check results
    """
    return system_monitor.get_health_check()


@monitoring_router.get("/user/{user_id}")
async def get_user_metrics(
    user_id: str,
    current_user: str = Depends(admin_required),
) -> Dict[str, Any]:
    """
    Get metrics for a specific user.

    This endpoint requires admin privileges.

    Args:
        user_id: The user ID to get metrics for

    Returns:
        Dictionary containing user-specific metrics
    """
    logger.info(f"Getting user metrics for user {user_id} by admin: {current_user}")

    # Get system metrics
    metrics = system_monitor.get_system_metrics()

    # Extract user-specific metrics
    user_metrics = {}

    # Get user directory size if available
    if "disk" in metrics and "data_dir" in metrics["disk"]:
        if "user_directories" in metrics["disk"]["data_dir"]:
            user_dirs = metrics["disk"]["data_dir"]["user_directories"]
            if user_id in user_dirs:
                user_metrics["storage"] = {
                    "size_bytes": user_dirs[user_id],
                    "size_mb": user_dirs[user_id] / (1024 * 1024),
                }

    # If no user-specific metrics found
    if not user_metrics:
        return {"message": f"No metrics found for user {user_id}"}

    return {
        "user_id": user_id,
        "metrics": user_metrics,
    }
