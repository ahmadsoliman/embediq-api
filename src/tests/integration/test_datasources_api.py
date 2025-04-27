"""
Integration tests for the Data Source Configuration API.
"""

import pytest
from fastapi.testclient import TestClient
import json
import logging
import os
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from uuid import UUID, uuid4
from datetime import datetime, timezone


from app.main import app
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

# Test client
client = TestClient(app)

# Mock token for testing
TEST_TOKEN = "test_token"
TEST_USER_ID = "test_user_123"


# Mock the validate_token dependency
@pytest.fixture
def mock_validate_token():
    """Mock the validate_token dependency to return a test user ID"""
    with patch("app.middleware.auth.validate_and_decode_token") as mock_validate:
        mock_validate.return_value = {"sub": TEST_USER_ID}
        yield


# Mock the ConfigurationStorageService
@pytest.fixture
def mock_storage_service():
    """Mock the ConfigurationStorageService methods"""
    with patch(
        "app.services.datasource_service.ConfigurationStorageService"
    ) as mock_service:
        # Create a test configuration
        test_config = {
            "id": str(uuid4()),
            "name": "Test Database",
            "type": "postgres",
            "description": "Test database configuration",
            "host": "localhost",
            "port": 5432,
            "database": "testdb",
            "username": "testuser",
            "password": "testpassword",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Mock the save_config method
        mock_service.save_config = AsyncMock(
            return_value=DatabaseDataSource(**test_config)
        )

        # Mock the get_config method
        mock_service.get_config = AsyncMock(
            return_value=DatabaseDataSource(**test_config)
        )

        # Mock the list_configs method
        mock_service.list_configs = AsyncMock(
            return_value=[DatabaseDataSource(**test_config)]
        )

        # Mock the update_config method
        mock_service.update_config = AsyncMock(
            return_value=DatabaseDataSource(**test_config)
        )

        # Mock the delete_config method
        mock_service.delete_config = AsyncMock(return_value=True)

        # Mock the get_user_datasources_dir method
        mock_service.get_user_datasources_dir = MagicMock(
            return_value="/tmp/test_user_123/datasources"
        )

        yield mock_service


# Mock the DataSourceValidationService
@pytest.fixture
def mock_validation_service():
    """Mock the DataSourceValidationService methods"""
    with patch(
        "app.services.datasource_validation_service.DataSourceValidationService"
    ) as mock_service:
        # Mock the validate_config method
        mock_service.validate_config = AsyncMock(
            return_value=ValidationResult(
                success=True,
                message="Validation successful",
                details={"database_type": "postgres"},
                warnings=[],
            )
        )

        yield mock_service


# Mock the datasource_registry
@pytest.fixture
def mock_registry():
    """Mock the datasource_registry"""
    with patch("app.services.datasource_registry.datasource_registry") as mock_reg:
        # Mock the list_type_info method
        mock_reg.list_type_info = MagicMock(
            return_value=[
                DataSourceTypeInfo(
                    type="postgres",
                    description="PostgreSQL database",
                    parameters=[
                        {
                            "name": "host",
                            "type": "string",
                            "required": False,
                            "description": "Database host",
                            "default": "localhost",
                        },
                        {
                            "name": "port",
                            "type": "integer",
                            "required": False,
                            "description": "Database port",
                            "default": 5432,
                        },
                        {
                            "name": "database",
                            "type": "string",
                            "required": True,
                            "description": "Database name",
                        },
                    ],
                ),
                DataSourceTypeInfo(
                    type="mysql",
                    description="MySQL database",
                    parameters=[
                        {
                            "name": "host",
                            "type": "string",
                            "required": False,
                            "description": "Database host",
                            "default": "localhost",
                        },
                        {
                            "name": "port",
                            "type": "integer",
                            "required": False,
                            "description": "Database port",
                            "default": 3306,
                        },
                        {
                            "name": "database",
                            "type": "string",
                            "required": True,
                            "description": "Database name",
                        },
                    ],
                ),
            ]
        )

        # Mock the get_type_info method
        mock_reg.get_type_info = MagicMock(
            return_value=DataSourceTypeInfo(
                type="postgres",
                description="PostgreSQL database",
                parameters=[
                    {
                        "name": "host",
                        "type": "string",
                        "required": False,
                        "description": "Database host",
                        "default": "localhost",
                    },
                    {
                        "name": "port",
                        "type": "integer",
                        "required": False,
                        "description": "Database port",
                        "default": 5432,
                    },
                    {
                        "name": "database",
                        "type": "string",
                        "required": True,
                        "description": "Database name",
                    },
                ],
            )
        )

        yield mock_reg


# Test creating a data source configuration
def test_create_datasource(mock_validate_token, mock_storage_service):
    """Test creating a data source configuration"""
    # Prepare request data
    config_data = {
        "name": "Test Database",
        "type": "postgres",
        "description": "Test database configuration",
        "host": "localhost",
        "port": 5432,
        "database": "testdb",
        "username": "testuser",
        "password": "testpassword",
    }

    # Send POST request to create a data source
    response = client.post(
        "/api/v1/datasources",
        json=config_data,
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )

    # Check response
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == config_data["name"]
    assert data["type"] == config_data["type"]
    assert data["description"] == config_data["description"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

    # Verify the service method was called with correct parameters
    mock_storage_service.save_config.assert_called_once()
    call_args = mock_storage_service.save_config.call_args[0]
    assert call_args[0] == TEST_USER_ID


# Test listing data source configurations
def test_list_datasources(mock_validate_token, mock_storage_service):
    """Test listing data source configurations"""
    # Send GET request to list data sources
    response = client.get(
        "/api/v1/datasources",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )

    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "datasources" in data
    assert "total" in data
    assert data["total"] == 1
    assert len(data["datasources"]) == 1

    # Verify the service method was called with correct parameters
    mock_storage_service.list_configs.assert_called_once_with(TEST_USER_ID)


# Test getting a specific data source configuration
def test_get_datasource(mock_validate_token, mock_storage_service):
    """Test getting a specific data source configuration"""
    # Get a test config ID
    test_config_id = str(uuid4())

    # Send GET request to get a specific data source
    response = client.get(
        f"/api/v1/datasources/{test_config_id}",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )

    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "name" in data
    assert "type" in data
    assert "description" in data
    assert "config" in data

    # Verify the service method was called with correct parameters
    mock_storage_service.get_config.assert_called_once_with(
        TEST_USER_ID, test_config_id
    )


# Test updating a data source configuration
def test_update_datasource(mock_validate_token, mock_storage_service):
    """Test updating a data source configuration"""
    # Get a test config ID
    test_config_id = str(uuid4())

    # Prepare request data
    config_data = {
        "id": test_config_id,
        "name": "Updated Database",
        "type": "postgres",
        "description": "Updated database configuration",
        "host": "localhost",
        "port": 5432,
        "database": "updateddb",
        "username": "updateduser",
        "password": "updatedpassword",
    }

    # Send PUT request to update a data source
    response = client.put(
        f"/api/v1/datasources/{test_config_id}",
        json=config_data,
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )

    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == config_data["name"]
    assert data["description"] == config_data["description"]

    # Verify the service method was called with correct parameters
    mock_storage_service.update_config.assert_called_once()
    call_args = mock_storage_service.update_config.call_args[0]
    assert call_args[0] == TEST_USER_ID
    assert call_args[1] == test_config_id


# Test deleting a data source configuration
def test_delete_datasource(mock_validate_token, mock_storage_service):
    """Test deleting a data source configuration"""
    # Get a test config ID
    test_config_id = str(uuid4())

    # Send DELETE request to delete a data source
    response = client.delete(
        f"/api/v1/datasources/{test_config_id}",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )

    # Check response
    assert response.status_code == 204

    # Verify the service method was called with correct parameters
    mock_storage_service.delete_config.assert_called_once_with(
        TEST_USER_ID, test_config_id
    )


# Test validating a data source configuration
def test_validate_datasource(
    mock_validate_token, mock_storage_service, mock_validation_service
):
    """Test validating a data source configuration"""
    # Get a test config ID
    test_config_id = str(uuid4())

    # Send POST request to validate a data source
    response = client.post(
        f"/api/v1/datasources/{test_config_id}/validate",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )

    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "message" in data
    assert "details" in data
    assert "warnings" in data
    assert data["success"] is True

    # Verify the service methods were called with correct parameters
    mock_storage_service.get_config.assert_called_with(TEST_USER_ID, test_config_id)
    mock_validation_service.validate_config.assert_called_once()


# Test listing data source types
def test_list_datasource_types(mock_validate_token, mock_registry):
    """Test listing data source types"""
    # Send GET request to list data source types
    response = client.get(
        "/api/v1/datasources/types",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )

    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "types" in data
    assert len(data["types"]) == 2
    assert data["types"][0]["type"] == "postgres"
    assert data["types"][1]["type"] == "mysql"

    # Verify the registry method was called
    mock_registry.list_type_info.assert_called_once()


# Test getting a specific data source type
def test_get_datasource_type(mock_validate_token, mock_registry):
    """Test getting a specific data source type"""
    # Send GET request to get a specific data source type
    response = client.get(
        "/api/v1/datasources/types/postgres",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )

    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "type" in data
    assert "description" in data
    assert "parameters" in data
    assert data["type"] == "postgres"

    # Verify the registry method was called with correct parameters
    mock_registry.get_type_info.assert_called_once_with("postgres")


# Test authentication requirement
def test_datasources_auth_required():
    """Test that datasources endpoints require authentication"""
    # Try to list data sources without authentication
    response = client.get("/api/v1/datasources")
    assert response.status_code == 401

    # Try to create a data source without authentication
    config_data = {
        "name": "Test Database",
        "type": "postgres",
        "description": "Test database configuration",
        "host": "localhost",
        "port": 5432,
        "database": "testdb",
    }
    response = client.post("/api/v1/datasources", json=config_data)
    assert response.status_code == 401

    # Try to get a data source without authentication
    test_config_id = str(uuid4())
    response = client.get(f"/api/v1/datasources/{test_config_id}")
    assert response.status_code == 401

    # Try to update a data source without authentication
    response = client.put(f"/api/v1/datasources/{test_config_id}", json=config_data)
    assert response.status_code == 401

    # Try to delete a data source without authentication
    response = client.delete(f"/api/v1/datasources/{test_config_id}")
    assert response.status_code == 401

    # Try to validate a data source without authentication
    response = client.post(f"/api/v1/datasources/{test_config_id}/validate")
    assert response.status_code == 401

    # Try to list data source types without authentication
    response = client.get("/api/v1/datasources/types")
    assert response.status_code == 401

    # Try to get a data source type without authentication
    response = client.get("/api/v1/datasources/types/postgres")
    assert response.status_code == 401


# Test validation error handling
def test_create_datasource_validation_error(mock_validate_token):
    """Test validation error handling when creating a data source"""
    # Prepare invalid request data (missing required fields)
    config_data = {
        "name": "Test Database",
        "type": "postgres",
        # Missing required 'database' field
    }

    # Send POST request to create a data source
    response = client.post(
        "/api/v1/datasources",
        json=config_data,
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )

    # Check response
    assert response.status_code == 422  # Unprocessable Entity
    data = response.json()
    assert "detail" in data


# Test handling non-existent data source
def test_get_nonexistent_datasource(mock_validate_token, mock_storage_service):
    """Test getting a non-existent data source"""
    # Mock get_config to return None
    mock_storage_service.get_config = AsyncMock(return_value=None)

    # Get a test config ID
    test_config_id = str(uuid4())

    # Send GET request to get a non-existent data source
    response = client.get(
        f"/api/v1/datasources/{test_config_id}",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )

    # Check response
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"]


# Test handling non-existent data source type
def test_get_nonexistent_datasource_type(mock_validate_token, mock_registry):
    """Test getting a non-existent data source type"""
    # Mock get_type_info to return None
    mock_registry.get_type_info = MagicMock(return_value=None)

    # Send GET request to get a non-existent data source type
    response = client.get(
        "/api/v1/datasources/types/nonexistent",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )

    # Check response
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"]


# Test filtering data sources by type
def test_list_datasources_with_filter(mock_validate_token, mock_storage_service):
    """Test listing data sources with type filter"""
    # Send GET request to list data sources with type filter
    response = client.get(
        "/api/v1/datasources?type=postgres",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )

    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "datasources" in data
    assert "total" in data

    # Verify the service method was called with correct parameters
    mock_storage_service.list_configs.assert_called_once_with(TEST_USER_ID)


# Test pagination for data sources list
def test_list_datasources_with_pagination(mock_validate_token, mock_storage_service):
    """Test listing data sources with pagination"""
    # Send GET request to list data sources with pagination
    response = client.get(
        "/api/v1/datasources?skip=0&limit=10",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )

    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "datasources" in data
    assert "total" in data

    # Verify the service method was called with correct parameters
    mock_storage_service.list_configs.assert_called_once_with(TEST_USER_ID)


# Test validation failure
def test_validate_datasource_failure(
    mock_validate_token, mock_storage_service, mock_validation_service
):
    """Test validation failure for a data source"""
    # Mock validate_config to return failure
    mock_validation_service.validate_config = AsyncMock(
        return_value=ValidationResult(
            success=False,
            message="Validation failed",
            details={"error": "Connection refused"},
            warnings=["Check your network settings"],
        )
    )

    # Get a test config ID
    test_config_id = str(uuid4())

    # Send POST request to validate a data source
    response = client.post(
        f"/api/v1/datasources/{test_config_id}/validate",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )

    # Check response
    assert response.status_code == 200  # Still 200 OK, but with success=False
    data = response.json()
    assert "success" in data
    assert "message" in data
    assert "details" in data
    assert "warnings" in data
    assert data["success"] is False
    assert "Validation failed" in data["message"]
    assert "Connection refused" in data["details"]["error"]
    assert "Check your network settings" in data["warnings"][0]
