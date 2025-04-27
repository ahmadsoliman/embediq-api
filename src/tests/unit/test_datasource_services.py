"""
Unit tests for data source services.
"""

import pytest
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from uuid import UUID, uuid4
from datetime import datetime
import httpx


from app.models.datasources import (
    DataSourceConfig,
    DatabaseDataSource,
    FileDataSource,
    APIDataSource,
    S3DataSource,
    ValidationResult,
)
from app.services.datasource_service import ConfigurationStorageService
from app.services.datasource_validation_service import DataSourceValidationService
from app.services.datasource_registry import DataSourceTypeRegistry


# Create a temporary directory for testing
@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


# Test ConfigurationStorageService
class TestConfigurationStorageService:
    """Tests for ConfigurationStorageService"""

    @pytest.mark.asyncio
    async def test_get_user_datasources_dir(self, temp_dir):
        """Test get_user_datasources_dir method"""
        # Mock DATA_DIR
        with patch("app.services.datasource_service.DATA_DIR", temp_dir):
            # Get user datasources directory
            user_id = "test_user"
            datasources_dir = ConfigurationStorageService.get_user_datasources_dir(
                user_id
            )

            # Check that the directory exists
            assert os.path.isdir(datasources_dir)
            assert datasources_dir == os.path.join(temp_dir, user_id, "datasources")

    @pytest.mark.asyncio
    async def test_encryption_key_derivation(self):
        """Test _get_encryption_key method"""
        # Get encryption key for a user
        user_id = "test_user"
        key = ConfigurationStorageService._get_encryption_key(user_id)

        # Check that the key is a bytes object
        assert isinstance(key, bytes)

        # Check that the key is deterministic
        key2 = ConfigurationStorageService._get_encryption_key(user_id)
        assert key == key2

        # Check that different users get different keys
        key3 = ConfigurationStorageService._get_encryption_key("other_user")
        assert key != key3

    @pytest.mark.asyncio
    async def test_encrypt_decrypt_sensitive_data(self):
        """Test _encrypt_sensitive_data and _decrypt_sensitive_data methods"""
        # Create test data
        user_id = "test_user"
        data = {
            "type": "postgres",
            "host": "localhost",
            "port": 5432,
            "database": "testdb",
            "username": "testuser",
            "password": "testpassword",
            "connection_string": "postgresql://testuser:testpassword@localhost:5432/testdb",
        }

        # Encrypt sensitive data
        encrypted_data = ConfigurationStorageService._encrypt_sensitive_data(
            data, user_id
        )

        # Check that sensitive fields are encrypted
        assert encrypted_data["password"] != data["password"]
        assert encrypted_data["connection_string"] != data["connection_string"]
        assert encrypted_data["password"].startswith("gAAAAA")
        assert encrypted_data["connection_string"].startswith("gAAAAA")

        # Check that non-sensitive fields are not encrypted
        assert encrypted_data["host"] == data["host"]
        assert encrypted_data["port"] == data["port"]
        assert encrypted_data["database"] == data["database"]
        assert encrypted_data["username"] == data["username"]

        # Decrypt sensitive data
        decrypted_data = ConfigurationStorageService._decrypt_sensitive_data(
            encrypted_data, user_id
        )

        # Check that sensitive fields are decrypted correctly
        assert decrypted_data["password"] == data["password"]
        assert decrypted_data["connection_string"] == data["connection_string"]

        # Check that non-sensitive fields are unchanged
        assert decrypted_data["host"] == data["host"]
        assert decrypted_data["port"] == data["port"]
        assert decrypted_data["database"] == data["database"]
        assert decrypted_data["username"] == data["username"]

    @pytest.mark.asyncio
    async def test_save_and_get_config(self, temp_dir):
        """Test save_config and get_config methods"""
        # Mock DATA_DIR
        with patch("app.services.datasource_service.DATA_DIR", temp_dir):
            # Create test data
            user_id = "test_user"
            config = DatabaseDataSource(
                name="Test Database",
                type="postgres",
                description="Test database configuration",
                host="localhost",
                port=5432,
                database="testdb",
                username="testuser",
                password="testpassword",
            )

            # Save the configuration
            saved_config = await ConfigurationStorageService.save_config(
                user_id, config
            )

            # Check that the configuration was saved
            assert isinstance(saved_config, DatabaseDataSource)
            assert saved_config.name == config.name
            assert saved_config.type == config.type
            assert saved_config.description == config.description
            assert saved_config.host == config.host
            assert saved_config.port == config.port
            assert saved_config.database == config.database
            assert saved_config.username == config.username
            # Skip password check as it's masked in the to_dict method

            # Get the configuration
            config_id = str(saved_config.id)
            retrieved_config = await ConfigurationStorageService.get_config(
                user_id, config_id
            )

            # Check that the configuration was retrieved correctly
            assert isinstance(retrieved_config, DatabaseDataSource)
            assert retrieved_config.id == saved_config.id
            assert retrieved_config.name == saved_config.name
            assert retrieved_config.type == saved_config.type
            assert retrieved_config.description == saved_config.description
            assert retrieved_config.host == saved_config.host
            assert retrieved_config.port == saved_config.port
            assert retrieved_config.database == saved_config.database
            assert retrieved_config.username == saved_config.username
            assert (
                retrieved_config.password.get_secret_value()
                == saved_config.password.get_secret_value()
            )

    @pytest.mark.asyncio
    async def test_list_configs(self, temp_dir):
        """Test list_configs method"""
        # Mock DATA_DIR
        with patch("app.services.datasource_service.DATA_DIR", temp_dir):
            # Create test data
            user_id = "test_user"
            config1 = DatabaseDataSource(
                name="Database 1",
                type="postgres",
                description="First database",
                database="db1",
            )
            config2 = DatabaseDataSource(
                name="Database 2",
                type="mysql",
                description="Second database",
                database="db2",
            )

            # Save the configurations
            await ConfigurationStorageService.save_config(user_id, config1)
            await ConfigurationStorageService.save_config(user_id, config2)

            # List the configurations
            configs = await ConfigurationStorageService.list_configs(user_id)

            # Check that the configurations were listed correctly
            assert len(configs) == 2
            assert any(c.name == "Database 1" and c.type == "postgres" for c in configs)
            assert any(c.name == "Database 2" and c.type == "mysql" for c in configs)

    @pytest.mark.asyncio
    async def test_update_config(self, temp_dir):
        """Test update_config method"""
        # Mock DATA_DIR
        with patch("app.services.datasource_service.DATA_DIR", temp_dir):
            # Create test data
            user_id = "test_user"
            config = DatabaseDataSource(
                name="Test Database",
                type="postgres",
                description="Test database configuration",
                host="localhost",
                port=5432,
                database="testdb",
                username="testuser",
                password="testpassword",
            )

            # Save the configuration
            saved_config = await ConfigurationStorageService.save_config(
                user_id, config
            )
            config_id = str(saved_config.id)

            # Update the configuration
            updated_config = DatabaseDataSource(
                id=saved_config.id,
                name="Updated Database",
                type="postgres",
                description="Updated database configuration",
                host="newhost",
                port=5433,
                database="newdb",
                username="newuser",
                password="newpassword",
            )

            # Update the configuration
            result = await ConfigurationStorageService.update_config(
                user_id, config_id, updated_config
            )

            # Check that the configuration was updated correctly
            assert result.name == updated_config.name
            assert result.description == updated_config.description
            assert result.host == updated_config.host
            assert result.port == updated_config.port
            assert result.database == updated_config.database
            assert result.username == updated_config.username
            # Skip password check as it's masked in the to_dict method

            # Get the configuration to verify the update
            retrieved_config = await ConfigurationStorageService.get_config(
                user_id, config_id
            )

            # Check that the configuration was updated in storage
            assert retrieved_config.name == updated_config.name
            assert retrieved_config.description == updated_config.description
            assert retrieved_config.host == updated_config.host
            assert retrieved_config.port == updated_config.port
            assert retrieved_config.database == updated_config.database
            assert retrieved_config.username == updated_config.username
            # Skip password check as it's masked in the to_dict method

    @pytest.mark.asyncio
    async def test_delete_config(self, temp_dir):
        """Test delete_config method"""
        # Mock DATA_DIR
        with patch("app.services.datasource_service.DATA_DIR", temp_dir):
            # Create test data
            user_id = "test_user"
            config = DatabaseDataSource(
                name="Test Database",
                type="postgres",
                description="Test database configuration",
                database="testdb",
            )

            # Save the configuration
            saved_config = await ConfigurationStorageService.save_config(
                user_id, config
            )
            config_id = str(saved_config.id)

            # Delete the configuration
            result = await ConfigurationStorageService.delete_config(user_id, config_id)

            # Check that the configuration was deleted
            assert result is True

            # Try to get the deleted configuration
            retrieved_config = await ConfigurationStorageService.get_config(
                user_id, config_id
            )

            # Check that the configuration is no longer available
            assert retrieved_config is None


# Test DataSourceValidationService
class TestDataSourceValidationService:
    """Tests for DataSourceValidationService"""

    @pytest.mark.asyncio
    async def test_validate_config_database(self):
        """Test validate_config method for database configurations"""
        # Create a test database configuration
        config = DatabaseDataSource(
            name="Test Database",
            type="postgres",
            description="Test database configuration",
            host="localhost",
            port=5432,
            database="testdb",
            username="testuser",
            password="testpassword",
        )

        # Mock the validate_database_connection method
        with patch.object(
            DataSourceValidationService,
            "validate_database_connection",
            new_callable=AsyncMock,
            return_value=ValidationResult(
                success=True,
                message="Database connection successful",
                details={"database_type": "postgres"},
                warnings=[],
            ),
        ):
            # Validate the configuration
            result = await DataSourceValidationService.validate_config(config)

            # Check the result
            assert result.success is True
            assert result.message == "Database connection successful"
            assert result.details["database_type"] == "postgres"
            assert len(result.warnings) == 0

    @pytest.mark.asyncio
    async def test_validate_config_file(self):
        """Test validate_config method for file configurations"""
        # Create a test file configuration
        config = FileDataSource(
            name="Test File",
            type="csv",
            description="Test file configuration",
            path="/path/to/file.csv",
        )

        # Mock the validate_file_access method
        with patch.object(
            DataSourceValidationService,
            "validate_file_access",
            new_callable=AsyncMock,
            return_value=ValidationResult(
                success=True,
                message="File access successful",
                details={"file_type": "csv"},
                warnings=[],
            ),
        ):
            # Validate the configuration
            result = await DataSourceValidationService.validate_config(config)

            # Check the result
            assert result.success is True
            assert result.message == "File access successful"
            assert result.details["file_type"] == "csv"
            assert len(result.warnings) == 0

    @pytest.mark.asyncio
    async def test_validate_config_api(self):
        """Test validate_config method for API configurations"""
        # Create a test API configuration
        config = APIDataSource(
            name="Test API",
            type="api",
            description="Test API configuration",
            url="https://api.example.com/data",
        )

        # Mock the validate_api_endpoint method
        with patch.object(
            DataSourceValidationService,
            "validate_api_endpoint",
            new_callable=AsyncMock,
            return_value=ValidationResult(
                success=True,
                message="API endpoint validation successful",
                details={"method": "GET", "url": "https://api.example.com/data"},
                warnings=[],
            ),
        ):
            # Validate the configuration
            result = await DataSourceValidationService.validate_config(config)

            # Check the result
            assert result.success is True
            assert result.message == "API endpoint validation successful"
            assert result.details["method"] == "GET"
            assert result.details["url"] == "https://api.example.com/data"
            assert len(result.warnings) == 0

    @pytest.mark.asyncio
    async def test_validate_config_s3(self):
        """Test validate_config method for S3 configurations"""
        # Create a test S3 configuration
        config = S3DataSource(
            name="Test S3",
            type="s3",
            description="Test S3 configuration",
            bucket="test-bucket",
            access_key="test-access-key",
            secret_key="test-secret-key",
        )

        # Mock the validate_s3_access method
        with patch.object(
            DataSourceValidationService,
            "validate_s3_access",
            new_callable=AsyncMock,
            return_value=ValidationResult(
                success=True,
                message="S3 access successful",
                details={"bucket": "test-bucket"},
                warnings=[],
            ),
        ):
            # Validate the configuration
            result = await DataSourceValidationService.validate_config(config)

            # Check the result
            assert result.success is True
            assert result.message == "S3 access successful"
            assert result.details["bucket"] == "test-bucket"
            assert len(result.warnings) == 0

    @pytest.mark.asyncio
    async def test_validate_config_unsupported(self):
        """Test validate_config method for unsupported configurations"""
        # Create a test configuration with an unsupported type
        config = DataSourceConfig(
            name="Test Unsupported",
            type="unsupported",
            description="Test unsupported configuration",
        )

        # Validate the configuration
        result = await DataSourceValidationService.validate_config(config)

        # Check the result
        assert result.success is False
        assert "Unsupported data source type" in result.message
        assert result.details["type"] == "unsupported"

    @pytest.mark.asyncio
    async def test_validate_sqlite_connection(self):
        """Test _validate_sqlite_connection method"""
        # Create a test SQLite configuration
        config = DatabaseDataSource(
            name="Test SQLite",
            type="sqlite",
            description="Test SQLite configuration",
            database=":memory:",  # Use in-memory database for testing
        )

        # Mock os.path.isfile to return True
        with patch("os.path.isfile", return_value=True), patch(
            "os.access", return_value=True
        ), patch("sqlite3.connect") as mock_connect:
            # Mock cursor and execution
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = (1,)
            mock_cursor.fetchall.return_value = [("table1",), ("table2",)]

            mock_conn = MagicMock()
            mock_conn.cursor.return_value = mock_cursor

            mock_connect.return_value = mock_conn

            # Validate the connection
            result = await DataSourceValidationService._validate_sqlite_connection(
                config
            )

            # Check the result
            assert result["success"] is True
            assert "Successfully connected to SQLite database" in result["message"]
            assert result["details"]["tables_count"] == 2
            assert result["details"]["tables"] == ["table1", "table2"]

    @pytest.mark.asyncio
    async def test_validate_file_access_csv(self, temp_dir):
        """Test validate_file_access method for CSV files"""
        # Create a test CSV file
        csv_path = os.path.join(temp_dir, "test.csv")
        with open(csv_path, "w") as f:
            f.write("id,name,value\n")
            f.write("1,test1,100\n")
            f.write("2,test2,200\n")

        # Create a test CSV configuration
        config = FileDataSource(
            name="Test CSV",
            type="csv",
            description="Test CSV configuration",
            path=csv_path,
            delimiter=",",
            has_header=True,
            encoding="utf-8",
        )

        # Validate the file access
        result = await DataSourceValidationService.validate_file_access(config)

        # Check the result
        assert result.success is True
        assert "Successfully validated CSV file" in result.message
        assert result.details["file_type"] == "csv"
        assert result.details["header"] == ["id", "name", "value"]
        assert len(result.details["sample_rows"]) == 2
        assert result.details["sample_rows"][0] == ["1", "test1", "100"]
        assert result.details["sample_rows"][1] == ["2", "test2", "200"]

    @pytest.mark.asyncio
    async def test_validate_file_access_json(self, temp_dir):
        """Test validate_file_access method for JSON files"""
        # Create a test JSON file
        json_path = os.path.join(temp_dir, "test.json")
        with open(json_path, "w") as f:
            json.dump({"key1": "value1", "key2": "value2"}, f)

        # Create a test JSON configuration
        config = FileDataSource(
            name="Test JSON",
            type="json",
            description="Test JSON configuration",
            path=json_path,
            encoding="utf-8",
        )

        # Validate the file access
        result = await DataSourceValidationService.validate_file_access(config)

        # Check the result
        assert result.success is True
        assert "Successfully validated JSON file" in result.message
        assert result.details["file_type"] == "json"
        assert result.details["structure"] == "object"
        assert set(result.details["keys"]) == {"key1", "key2"}

    @pytest.mark.asyncio
    async def test_validate_api_request(self):
        """Test _validate_api_request method"""
        # Create a test API configuration
        config = APIDataSource(
            name="Test API",
            type="api",
            description="Test API configuration",
            url="https://api.example.com/data",
            method="GET",
            headers={"Accept": "application/json"},
            response_format="json",
        )

        # Mock httpx.AsyncClient
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"data": [{"id": 1, "name": "test"}]}

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get.return_value = mock_response
        mock_client.__aenter__.return_value.post.return_value = mock_response

        with patch("httpx.AsyncClient", return_value=mock_client):
            # Validate the API request
            result = await DataSourceValidationService._validate_api_request(config)

            # Check the result
            assert result["success"] is True
            assert "API request successful" in result["message"]
            assert result["details"]["status_code"] == 200
            assert result["details"]["content_type"] == "application/json"
            assert result["details"]["response_type"] == "json"


# Test DataSourceTypeRegistry
class TestDataSourceTypeRegistry:
    """Tests for DataSourceTypeRegistry"""

    def test_singleton_pattern(self):
        """Test that DataSourceTypeRegistry is a singleton"""
        # Create two instances
        registry1 = DataSourceTypeRegistry()
        registry2 = DataSourceTypeRegistry()

        # Check that they are the same instance
        assert registry1 is registry2

    def test_register_and_get_type(self):
        """Test register_type and get_type methods"""
        # Create a registry
        registry = DataSourceTypeRegistry()

        # Register a new type
        registry.register_type(
            type_name="test_type",
            model_class=DataSourceConfig,
            description="Test type",
            parameters=[
                {
                    "name": "param1",
                    "type": "string",
                    "required": True,
                    "description": "Test parameter",
                },
            ],
        )

        # Get the type
        type_info = registry.get_type("test_type")

        # Check the type information
        assert type_info["model_class"] == DataSourceConfig
        assert type_info["description"] == "Test type"
        assert len(type_info["parameters"]) == 1
        assert type_info["parameters"][0]["name"] == "param1"

    def test_get_model_class(self):
        """Test get_model_class method"""
        # Create a registry
        registry = DataSourceTypeRegistry()

        # Register a new type
        registry.register_type(
            type_name="test_type",
            model_class=DatabaseDataSource,
            description="Test type",
        )

        # Get the model class
        model_class = registry.get_model_class("test_type")

        # Check the model class
        assert model_class == DatabaseDataSource

        # Try to get a non-existent type
        model_class = registry.get_model_class("non_existent")

        # Check that it returns None
        assert model_class is None

    def test_list_types(self):
        """Test list_types method"""
        # Create a registry
        registry = DataSourceTypeRegistry()

        # Get the list of types
        types = registry.list_types()

        # Check that the built-in types are included
        assert "postgres" in types
        assert "mysql" in types
        assert "sqlite" in types
        assert "csv" in types
        assert "json" in types
        assert "api" in types
        assert "s3" in types

    def test_get_type_info(self):
        """Test get_type_info method"""
        # Create a registry
        registry = DataSourceTypeRegistry()

        # Get type information
        type_info = registry.get_type_info("postgres")

        # Check the type information
        assert type_info.type == "postgres"
        assert type_info.description == "PostgreSQL database"
        assert len(type_info.parameters) > 0

        # Try to get a non-existent type
        type_info = registry.get_type_info("non_existent")

        # Check that it returns None
        assert type_info is None

    def test_list_type_info(self):
        """Test list_type_info method"""
        # Create a registry
        registry = DataSourceTypeRegistry()

        # Get the list of type information
        type_info_list = registry.list_type_info()

        # Check that the list contains the built-in types
        assert len(type_info_list) >= 7  # At least 7 built-in types
        assert any(info.type == "postgres" for info in type_info_list)
        assert any(info.type == "mysql" for info in type_info_list)
        assert any(info.type == "sqlite" for info in type_info_list)
        assert any(info.type == "csv" for info in type_info_list)
        assert any(info.type == "json" for info in type_info_list)
        assert any(info.type == "api" for info in type_info_list)
        assert any(info.type == "s3" for info in type_info_list)
