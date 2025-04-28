"""
LightRAG configuration module for EmbedIQ backend.

This module provides configuration options for LightRAG parameters such as
chunk sizes, embedding model parameters, and graph traversal depth.
"""

import os
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator

from app.config.app_config import (
    CHUNK_SIZE,
    GRAPH_TRAVERSAL_DEPTH,
    CACHE_ENABLED,
    CACHE_SIZE,
    VECTOR_DIMENSION,
    MAX_TOKEN_SIZE,
)

logger = logging.getLogger(__name__)


class LightRAGConfig(BaseModel):
    """
    Configuration model for LightRAG parameters.
    """

    chunk_size: int = Field(default=CHUNK_SIZE, ge=100, le=5000)
    graph_traversal_depth: int = Field(default=GRAPH_TRAVERSAL_DEPTH, ge=1, le=5)
    cache_enabled: bool = Field(default=CACHE_ENABLED)
    cache_size: int = Field(default=CACHE_SIZE, ge=10, le=10000)
    vector_dimension: int = Field(default=VECTOR_DIMENSION, ge=768, le=4096)
    max_token_size: int = Field(default=MAX_TOKEN_SIZE, ge=1024, le=32768)

    @field_validator("chunk_size")
    def validate_chunk_size(cls, v):
        """Validate chunk size"""
        if v < 100:
            logger.warning(f"Chunk size {v} is too small, setting to 100")
            return 100
        if v > 5000:
            logger.warning(f"Chunk size {v} is too large, setting to 5000")
            return 5000
        return v

    @field_validator("graph_traversal_depth")
    def validate_graph_traversal_depth(cls, v):
        """Validate graph traversal depth"""
        if v < 1:
            logger.warning(f"Graph traversal depth {v} is too small, setting to 1")
            return 1
        if v > 5:
            logger.warning(f"Graph traversal depth {v} is too large, setting to 5")
            return 5
        return v

    @field_validator("cache_size")
    def validate_cache_size(cls, v):
        """Validate cache size"""
        if v < 10:
            logger.warning(f"Cache size {v} is too small, setting to 10")
            return 10
        if v > 10000:
            logger.warning(f"Cache size {v} is too large, setting to 10000")
            return 10000
        return v


# Global variables for configuration
# Default configuration
default_config: LightRAGConfig = None
# User-specific configurations
user_configs: Dict[str, LightRAGConfig] = {}

# Initialize default configuration
default_config = LightRAGConfig()


def get_lightrag_config(user_id: Optional[str] = None) -> LightRAGConfig:
    """
    Get LightRAG configuration for a user.

    Args:
        user_id: The user ID (optional)

    Returns:
        LightRAG configuration for the user or default configuration
    """
    if user_id and user_id in user_configs:
        return user_configs[user_id]
    return default_config


def set_lightrag_config(
    config: Dict[str, Any], user_id: Optional[str] = None
) -> LightRAGConfig:
    """
    Set LightRAG configuration for a user.

    Args:
        config: Configuration dictionary
        user_id: The user ID (optional)

    Returns:
        Updated LightRAG configuration
    """
    # Create a new configuration by merging with existing config
    if user_id and user_id in user_configs:
        # Update existing user config
        current_config = user_configs[user_id].model_dump()
        current_config.update(config)
        new_config = LightRAGConfig(**current_config)
    else:
        # Create new config based on default
        current_config = default_config.model_dump()
        current_config.update(config)
        new_config = LightRAGConfig(**current_config)

    # Store the configuration
    if user_id:
        user_configs[user_id] = new_config
        logger.info(f"Updated LightRAG configuration for user {user_id}")
    else:
        # Update default configuration (no need for global here since we're not reassigning)
        default_config = new_config
        logger.info("Updated default LightRAG configuration")

    return new_config


def reset_lightrag_config(user_id: Optional[str] = None) -> None:
    """
    Reset LightRAG configuration to default.

    Args:
        user_id: The user ID (optional)
    """
    if user_id and user_id in user_configs:
        del user_configs[user_id]
        logger.info(f"Reset LightRAG configuration for user {user_id}")
    elif user_id is None:
        # Reset default configuration (no need for global here since we're not reassigning)
        default_config = LightRAGConfig()
        user_configs.clear()
        logger.info("Reset all LightRAG configurations to default")
