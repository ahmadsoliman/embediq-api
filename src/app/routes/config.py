"""
Configuration API endpoints for EmbedIQ backend.

This module provides API endpoints for managing LightRAG configuration.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import Dict, Any, Optional
from app.middleware.auth import validate_token, admin_required
from app.config.lightrag_config import (
    get_lightrag_config,
    set_lightrag_config,
    reset_lightrag_config,
    LightRAGConfig,
)

logger = logging.getLogger(__name__)

# Create router
config_router = APIRouter(
    prefix="/config",
    tags=["config"],
)


@config_router.get("/lightrag")
async def get_lightrag_configuration(
    user_id: str = Depends(validate_token),
) -> LightRAGConfig:
    """
    Get LightRAG configuration for the authenticated user.

    Returns:
        LightRAG configuration
    """
    logger.info(f"Getting LightRAG configuration for user {user_id}")
    return get_lightrag_config(user_id=user_id)


@config_router.put("/lightrag")
async def update_lightrag_configuration(
    config: Dict[str, Any] = Body(...),
    user_id: str = Depends(validate_token),
) -> LightRAGConfig:
    """
    Update LightRAG configuration for the authenticated user.

    Args:
        config: Configuration dictionary

    Returns:
        Updated LightRAG configuration
    """
    logger.info(f"Updating LightRAG configuration for user {user_id}")
    return set_lightrag_config(config=config, user_id=user_id)


@config_router.delete("/lightrag")
async def reset_lightrag_configuration(
    user_id: str = Depends(validate_token),
) -> Dict[str, Any]:
    """
    Reset LightRAG configuration to default for the authenticated user.

    Returns:
        Success message
    """
    logger.info(f"Resetting LightRAG configuration for user {user_id}")
    reset_lightrag_config(user_id=user_id)
    return {"message": "LightRAG configuration reset to default"}


@config_router.get("/lightrag/default")
async def get_default_lightrag_configuration(
    current_user: str = Depends(admin_required),
) -> LightRAGConfig:
    """
    Get default LightRAG configuration.

    This endpoint requires admin privileges.

    Returns:
        Default LightRAG configuration
    """
    logger.info(
        f"Getting default LightRAG configuration for admin user: {current_user}"
    )
    return get_lightrag_config()


@config_router.put("/lightrag/default")
async def update_default_lightrag_configuration(
    config: Dict[str, Any] = Body(...),
    current_user: str = Depends(admin_required),
) -> LightRAGConfig:
    """
    Update default LightRAG configuration.

    This endpoint requires admin privileges.

    Args:
        config: Configuration dictionary

    Returns:
        Updated default LightRAG configuration
    """
    logger.info(
        f"Updating default LightRAG configuration for admin user: {current_user}"
    )
    return set_lightrag_config(config=config)


@config_router.delete("/lightrag/default")
async def reset_default_lightrag_configuration(
    current_user: str = Depends(admin_required),
) -> Dict[str, Any]:
    """
    Reset default LightRAG configuration.

    This endpoint requires admin privileges.

    Returns:
        Success message
    """
    logger.info(
        f"Resetting default LightRAG configuration for admin user: {current_user}"
    )
    reset_lightrag_config()
    return {"message": "Default LightRAG configuration reset"}
