"""
API routes for data source configuration.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from uuid import UUID

from app.middleware.auth import validate_token
from app.models.datasources import (
    DataSourceConfig,
    DatabaseDataSource,
    FileDataSource,
    APIDataSource,
    S3DataSource,
    ValidationResult,
    DataSourceResponse,
    DataSourceList,
    DataSourceTypeInfo,
    DataSourceTypeList,
)
from app.services.datasource_service import ConfigurationStorageService
from app.services.datasource_validation_service import DataSourceValidationService
from app.services.datasource_registry import datasource_registry

logger = logging.getLogger(__name__)

# Create router
datasources_router = APIRouter(tags=["datasources"])


@datasources_router.post(
    "",
    response_model=DataSourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new data source configuration",
    description="Create a new data source configuration for the authenticated user.",
)
async def create_datasource(
    config: DataSourceConfig, user_id: str = Depends(validate_token)
):
    """
    Create a new data source configuration

    Args:
        config: The data source configuration
        user_id: The authenticated user ID

    Returns:
        The created data source configuration
    """
    try:
        # Save the configuration
        saved_config = await ConfigurationStorageService.save_config(user_id, config)

        # Convert to response model
        response = DataSourceResponse(
            id=saved_config.id,
            name=saved_config.name,
            type=saved_config.type,
            description=saved_config.description,
            created_at=saved_config.created_at,
            updated_at=saved_config.updated_at,
            config=saved_config.to_dict(),
        )

        logger.info(
            f"Created data source configuration {saved_config.id} for user {user_id}"
        )
        return response
    except Exception as e:
        logger.error(f"Error creating data source configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating data source configuration: {str(e)}",
        )


@datasources_router.get(
    "",
    response_model=DataSourceList,
    summary="List data source configurations",
    description="List all data source configurations for the authenticated user.",
)
async def list_datasources(
    user_id: str = Depends(validate_token),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(
        100, ge=1, le=100, description="Maximum number of items to return"
    ),
    type: Optional[str] = Query(None, description="Filter by data source type"),
):
    """
    List data source configurations

    Args:
        user_id: The authenticated user ID
        skip: Number of items to skip
        limit: Maximum number of items to return
        type: Filter by data source type

    Returns:
        A list of data source configurations
    """
    try:
        # Get all configurations
        configs = await ConfigurationStorageService.list_configs(user_id)

        # Filter by type if specified
        if type:
            configs = [config for config in configs if config.type == type]

        # Get total count
        total = len(configs)

        # Apply pagination
        configs = configs[skip : skip + limit]

        # Convert to response models
        datasources = [
            DataSourceResponse(
                id=config.id,
                name=config.name,
                type=config.type,
                description=config.description,
                created_at=config.created_at,
                updated_at=config.updated_at,
                config=config.to_dict(),
            )
            for config in configs
        ]

        logger.info(
            f"Retrieved {len(datasources)} data source configurations for user {user_id}"
        )
        return DataSourceList(datasources=datasources, total=total)
    except Exception as e:
        logger.error(f"Error listing data source configurations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing data source configurations: {str(e)}",
        )


@datasources_router.get(
    "/{id}",
    response_model=DataSourceResponse,
    summary="Get a data source configuration",
    description="Get a specific data source configuration by ID.",
)
async def get_datasource(
    id: UUID = Path(..., description="Data source configuration ID"),
    user_id: str = Depends(validate_token),
):
    """
    Get a data source configuration

    Args:
        id: The data source configuration ID
        user_id: The authenticated user ID

    Returns:
        The data source configuration
    """
    try:
        # Get the configuration
        config = await ConfigurationStorageService.get_config(user_id, str(id))

        # Check if the configuration exists
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Data source configuration {id} not found",
            )

        # Convert to response model
        response = DataSourceResponse(
            id=config.id,
            name=config.name,
            type=config.type,
            description=config.description,
            created_at=config.created_at,
            updated_at=config.updated_at,
            config=config.to_dict(),
        )

        logger.info(f"Retrieved data source configuration {id} for user {user_id}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving data source configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving data source configuration: {str(e)}",
        )


@datasources_router.put(
    "/{id}",
    response_model=DataSourceResponse,
    summary="Update a data source configuration",
    description="Update a specific data source configuration by ID.",
)
async def update_datasource(
    config: DataSourceConfig,
    id: UUID = Path(..., description="Data source configuration ID"),
    user_id: str = Depends(validate_token),
):
    """
    Update a data source configuration

    Args:
        config: The updated data source configuration
        id: The data source configuration ID
        user_id: The authenticated user ID

    Returns:
        The updated data source configuration
    """
    try:
        # Ensure ID in path matches ID in body
        if str(id) != str(config.id):
            config.id = id

        # Update the configuration
        updated_config = await ConfigurationStorageService.update_config(
            user_id, str(id), config
        )

        # Check if the configuration exists
        if not updated_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Data source configuration {id} not found",
            )

        # Convert to response model
        response = DataSourceResponse(
            id=updated_config.id,
            name=updated_config.name,
            type=updated_config.type,
            description=updated_config.description,
            created_at=updated_config.created_at,
            updated_at=updated_config.updated_at,
            config=updated_config.to_dict(),
        )

        logger.info(f"Updated data source configuration {id} for user {user_id}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating data source configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating data source configuration: {str(e)}",
        )


@datasources_router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a data source configuration",
    description="Delete a specific data source configuration by ID.",
)
async def delete_datasource(
    id: UUID = Path(..., description="Data source configuration ID"),
    user_id: str = Depends(validate_token),
):
    """
    Delete a data source configuration

    Args:
        id: The data source configuration ID
        user_id: The authenticated user ID
    """
    try:
        # Delete the configuration
        deleted = await ConfigurationStorageService.delete_config(user_id, str(id))

        # Check if the configuration exists
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Data source configuration {id} not found",
            )

        logger.info(f"Deleted data source configuration {id} for user {user_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting data source configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting data source configuration: {str(e)}",
        )


@datasources_router.post(
    "/{id}/validate",
    response_model=ValidationResult,
    summary="Validate a data source configuration",
    description="Validate a specific data source configuration by testing the connection.",
)
async def validate_datasource(
    id: UUID = Path(..., description="Data source configuration ID"),
    user_id: str = Depends(validate_token),
):
    """
    Validate a data source configuration

    Args:
        id: The data source configuration ID
        user_id: The authenticated user ID

    Returns:
        The validation result
    """
    try:
        # Get the configuration
        config = await ConfigurationStorageService.get_config(user_id, str(id))

        # Check if the configuration exists
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Data source configuration {id} not found",
            )

        # Validate the configuration
        result = await DataSourceValidationService.validate_config(config)

        logger.info(
            f"Validated data source configuration {id} for user {user_id}: {result.success}"
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating data source configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating data source configuration: {str(e)}",
        )


@datasources_router.get(
    "/types",
    response_model=DataSourceTypeList,
    summary="List data source types",
    description="List all supported data source types and their parameters.",
)
async def list_datasource_types(
    user_id: str = Depends(validate_token),
):
    """
    List data source types

    Args:
        user_id: The authenticated user ID

    Returns:
        A list of data source types
    """
    try:
        # Get all type information
        types = datasource_registry.list_type_info()

        # Ensure types is a list (even if empty)
        if types is None:
            types = []

        logger.info(f"Retrieved {len(types)} data source types for user {user_id}")
        return DataSourceTypeList(types=types)
    except Exception as e:
        logger.error(f"Error listing data source types: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing data source types: {str(e)}",
        )


@datasources_router.get(
    "/types/{type_name}",
    response_model=DataSourceTypeInfo,
    summary="Get data source type information",
    description="Get information about a specific data source type.",
)
async def get_datasource_type(
    type_name: str = Path(..., description="Data source type name"),
    user_id: str = Depends(validate_token),
):
    """
    Get data source type information

    Args:
        type_name: The data source type name
        user_id: The authenticated user ID

    Returns:
        Information about the data source type
    """
    try:
        # Get type information
        type_info = datasource_registry.get_type_info(type_name)

        # Check if the type exists
        if not type_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Data source type {type_name} not found",
            )

        logger.info(f"Retrieved data source type {type_name} for user {user_id}")
        return type_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving data source type: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving data source type: {str(e)}",
        )
