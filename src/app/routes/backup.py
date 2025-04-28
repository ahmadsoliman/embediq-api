"""
Backup API endpoints for EmbedIQ backend.

This module provides API endpoints for managing backups and data replication.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from typing import Dict, Any, List, Optional
from app.middleware.auth import admin_required
from app.backup.backup_service import get_backup_service

logger = logging.getLogger(__name__)

# Create router
backup_router = APIRouter(
    prefix="/backup",
    tags=["backup"],
)


@backup_router.get("/status")
async def get_backup_status(
    current_user: str = Depends(admin_required),
) -> Dict[str, Any]:
    """
    Get backup status.

    This endpoint requires admin privileges.

    Returns:
        Dictionary containing backup status
    """
    logger.info(f"Getting backup status for admin user: {current_user}")
    backup_service = get_backup_service()
    return await backup_service.get_backup_status()


@backup_router.get("/history")
async def get_backup_history(
    limit: int = Query(10, ge=1, le=100),
    current_user: str = Depends(admin_required),
) -> List[Dict[str, Any]]:
    """
    Get backup history.

    This endpoint requires admin privileges.

    Args:
        limit: Maximum number of history items to return

    Returns:
        List of backup history items
    """
    logger.info(f"Getting backup history for admin user: {current_user}")
    backup_service = get_backup_service()
    return await backup_service.get_backup_history(limit=limit)


@backup_router.post("/trigger")
async def trigger_backup(
    current_user: str = Depends(admin_required),
) -> Dict[str, Any]:
    """
    Trigger a manual backup.

    This endpoint requires admin privileges.

    Returns:
        Dictionary containing backup results
    """
    logger.info(f"Triggering manual backup for admin user: {current_user}")
    backup_service = get_backup_service()
    return await backup_service.trigger_backup()


@backup_router.post("/restore/{backup_id}")
async def restore_backup(
    backup_id: str = Path(..., description="The backup ID to restore from"),
    current_user: str = Depends(admin_required),
) -> Dict[str, Any]:
    """
    Restore from a backup.

    This endpoint requires admin privileges.

    Args:
        backup_id: The backup ID to restore from

    Returns:
        Dictionary containing restore results
    """
    logger.info(f"Restoring from backup {backup_id} for admin user: {current_user}")
    backup_service = get_backup_service()
    return await backup_service.restore_backup(backup_id=backup_id)


@backup_router.post("/start")
async def start_backup_scheduler(
    current_user: str = Depends(admin_required),
) -> Dict[str, Any]:
    """
    Start the backup scheduler.

    This endpoint requires admin privileges.

    Returns:
        Success message
    """
    logger.info(f"Starting backup scheduler for admin user: {current_user}")
    backup_service = get_backup_service()
    await backup_service.start_backup_scheduler()
    return {"message": "Backup scheduler started successfully"}


@backup_router.post("/stop")
async def stop_backup_scheduler(
    current_user: str = Depends(admin_required),
) -> Dict[str, Any]:
    """
    Stop the backup scheduler.

    This endpoint requires admin privileges.

    Returns:
        Success message
    """
    logger.info(f"Stopping backup scheduler for admin user: {current_user}")
    backup_service = get_backup_service()
    await backup_service.stop_backup_scheduler()
    return {"message": "Backup scheduler stopped successfully"}
