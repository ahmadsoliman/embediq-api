"""
Unit tests for data source configuration models.
"""

import pytest
from pydantic import ValidationError
from uuid import UUID, uuid4
from datetime import datetime, timezone
import json


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


# Test base DataSourceConfig model
def test_datasource_config_base():
    """Test the base DataSourceConfig model"""
    # Create a valid config
    config = DataSourceConfig(
        name="Test Config",
        type="postgres",
        description="Test description",
        database="testdb",  # Add database field for postgres type
    )

    # Check fields
    assert config.name == "Test Config"
    assert config.type == "postgres"
    assert config.description == "Test description"
    assert isinstance(config.id, UUID)
    assert isinstance(config.created_at, datetime)
    assert isinstance(config.updated_at, datetime)

    # Test to_dict method
    config_dict = config.to_dict()
    assert isinstance(config_dict, dict)
    assert config_dict["name"] == "Test Config"
    assert config_dict["type"] == "postgres"
    assert config_dict["description"] == "Test description"
    assert isinstance(config_dict["id"], str)
    assert isinstance(config_dict["created_at"], str)
    assert isinstance(config_dict["updated_at"], str)

    # Test from_dict method
    config2 = DataSourceConfig.from_dict(config_dict)
    assert config2.name == config.name
    assert config2.type == config.type
    assert config2.description == config.description
    assert str(config2.id) == config_dict["id"]


# Test DatabaseDataSource model
def test_database_datasource():
    """Test the DatabaseDataSource model"""
    # Create a valid PostgreSQL config
    postgres_config = DatabaseDataSource(
        name="PostgreSQL DB",
        type="postgres",
        description="PostgreSQL database",
        host="localhost",
        port=5432,
        database="testdb",
        username="testuser",
        password="testpassword",
    )

    # Check fields
    assert postgres_config.name == "PostgreSQL DB"
    assert postgres_config.type == "postgres"
    assert postgres_config.host == "localhost"
    assert postgres_config.port == 5432
    assert postgres_config.database == "testdb"
    assert postgres_config.username == "testuser"
    assert postgres_config.password.get_secret_value() == "testpassword"

    # Test to_dict method (should mask password)
    config_dict = postgres_config.to_dict()
    assert config_dict["password"] == "********"

    # Create a valid MySQL config
    mysql_config = DatabaseDataSource(
        name="MySQL DB",
        type="mysql",
        description="MySQL database",
        host="localhost",
        port=3306,
        database="testdb",
        username="testuser",
        password="testpassword",
    )

    assert mysql_config.type == "mysql"
    assert mysql_config.port == 3306

    # Create a valid SQLite config
    sqlite_config = DatabaseDataSource(
        name="SQLite DB",
        type="sqlite",
        description="SQLite database",
        database="/path/to/db.sqlite",
    )

    assert sqlite_config.type == "sqlite"
    assert sqlite_config.database == "/path/to/db.sqlite"

    # Test connection string alternative
    conn_string_config = DatabaseDataSource(
        name="Connection String DB",
        type="postgres",
        description="Database with connection string",
        connection_string="postgresql://user:pass@localhost:5432/db",
    )

    assert (
        conn_string_config.connection_string
        == "postgresql://user:pass@localhost:5432/db"
    )


# Test validation for DatabaseDataSource
def test_database_datasource_validation():
    """Test validation for DatabaseDataSource"""
    # Test missing required fields
    with pytest.raises(ValidationError):
        DatabaseDataSource(
            name="Invalid DB",
            type="postgres",
            # Missing database
        )

    # Test invalid connection string format
    with pytest.raises(ValidationError):
        DatabaseDataSource(
            name="Invalid Connection",
            type="postgres",
            connection_string="invalid://connection/string",
        )


# Test FileDataSource model
def test_file_datasource():
    """Test the FileDataSource model"""
    # Create a valid CSV config
    csv_config = FileDataSource(
        name="CSV File",
        type="csv",
        description="CSV file data source",
        path="/path/to/file.csv",
        delimiter=",",
        has_header=True,
        encoding="utf-8",
    )

    # Check fields
    assert csv_config.name == "CSV File"
    assert csv_config.type == "csv"
    assert csv_config.path == "/path/to/file.csv"
    assert csv_config.delimiter == ","
    assert csv_config.has_header is True
    assert csv_config.encoding == "utf-8"

    # Create a valid JSON config
    json_config = FileDataSource(
        name="JSON File",
        type="json",
        description="JSON file data source",
        path="/path/to/file.json",
        encoding="utf-8",
    )

    assert json_config.type == "json"
    assert json_config.path == "/path/to/file.json"


# Test validation for FileDataSource
def test_file_datasource_validation():
    """Test validation for FileDataSource"""
    # Test missing required fields
    with pytest.raises(ValidationError):
        FileDataSource(
            name="Invalid File",
            type="csv",
            # Missing path
        )


# Test APIDataSource model
def test_api_datasource():
    """Test the APIDataSource model"""
    # Create a valid API config with basic auth
    basic_auth_config = APIDataSource(
        name="API with Basic Auth",
        type="api",
        description="API with basic authentication",
        url="https://api.example.com/data",
        method="GET",
        headers={"Accept": "application/json"},
        auth_type="basic",
        auth_username="apiuser",
        auth_password="apipassword",
    )

    # Check fields
    assert basic_auth_config.name == "API with Basic Auth"
    assert basic_auth_config.type == "api"
    assert basic_auth_config.url == "https://api.example.com/data"
    assert basic_auth_config.method == "GET"
    assert basic_auth_config.headers == {"Accept": "application/json"}
    assert basic_auth_config.auth_type == "basic"
    assert basic_auth_config.auth_username == "apiuser"
    assert basic_auth_config.auth_password.get_secret_value() == "apipassword"

    # Test to_dict method (should mask sensitive data)
    config_dict = basic_auth_config.to_dict()
    assert config_dict["auth_password"] == "********"

    # Create a valid API config with bearer token
    bearer_auth_config = APIDataSource(
        name="API with Bearer Token",
        type="api",
        description="API with bearer token authentication",
        url="https://api.example.com/data",
        method="GET",
        auth_type="bearer",
        auth_token="abcdef123456",
    )

    assert bearer_auth_config.auth_type == "bearer"
    assert bearer_auth_config.auth_token.get_secret_value() == "abcdef123456"

    # Create a valid API config with API key
    api_key_config = APIDataSource(
        name="API with API Key",
        type="api",
        description="API with API key authentication",
        url="https://api.example.com/data",
        method="GET",
        auth_type="api_key",
        api_key="xyz789",
        api_key_name="X-API-Key",
        api_key_location="header",
    )

    assert api_key_config.auth_type == "api_key"
    assert api_key_config.api_key.get_secret_value() == "xyz789"
    assert api_key_config.api_key_name == "X-API-Key"
    assert api_key_config.api_key_location == "header"


# Test validation for APIDataSource
def test_api_datasource_validation():
    """Test validation for APIDataSource"""
    # Test missing required fields
    with pytest.raises(ValidationError):
        APIDataSource(
            name="Invalid API",
            type="api",
            # Missing url
        )

    # Test invalid URL format
    with pytest.raises(ValidationError):
        APIDataSource(
            name="Invalid URL",
            type="api",
            url="not-a-valid-url",
        )

    # Test missing auth credentials for basic auth
    with pytest.raises(ValidationError):
        APIDataSource(
            name="Invalid Basic Auth",
            type="api",
            url="https://api.example.com/data",
            auth_type="basic",
            # Missing auth_username and auth_password
        )

    # Test missing token for bearer auth
    with pytest.raises(ValidationError):
        APIDataSource(
            name="Invalid Bearer Auth",
            type="api",
            url="https://api.example.com/data",
            auth_type="bearer",
            # Missing auth_token
        )

    # Test missing API key for api_key auth
    with pytest.raises(ValidationError):
        APIDataSource(
            name="Invalid API Key Auth",
            type="api",
            url="https://api.example.com/data",
            auth_type="api_key",
            # Missing api_key and api_key_name
        )


# Test S3DataSource model
def test_s3_datasource():
    """Test the S3DataSource model"""
    # Create a valid S3 config with credentials
    s3_config = S3DataSource(
        name="S3 Bucket",
        type="s3",
        description="S3 bucket data source",
        bucket="my-bucket",
        prefix="data/",
        region="us-west-2",
        access_key="AKIAIOSFODNN7EXAMPLE",
        secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    )

    # Check fields
    assert s3_config.name == "S3 Bucket"
    assert s3_config.type == "s3"
    assert s3_config.bucket == "my-bucket"
    assert s3_config.prefix == "data/"
    assert s3_config.region == "us-west-2"
    assert s3_config.access_key == "AKIAIOSFODNN7EXAMPLE"
    assert (
        s3_config.secret_key.get_secret_value()
        == "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    )

    # Test to_dict method (should mask secret key)
    config_dict = s3_config.to_dict()
    assert config_dict["secret_key"] == "********"

    # Create a valid S3 config with instance profile
    instance_profile_config = S3DataSource(
        name="S3 with Instance Profile",
        type="s3",
        description="S3 bucket using instance profile",
        bucket="my-bucket",
        use_instance_profile=True,
    )

    assert instance_profile_config.use_instance_profile is True
    assert instance_profile_config.bucket == "my-bucket"


# Test validation for S3DataSource
def test_s3_datasource_validation():
    """Test validation for S3DataSource"""
    # Test missing required fields
    with pytest.raises(ValidationError):
        S3DataSource(
            name="Invalid S3",
            type="s3",
            # Missing bucket
        )

    # Test missing authentication
    with pytest.raises(ValidationError):
        S3DataSource(
            name="Invalid S3 Auth",
            type="s3",
            bucket="my-bucket",
            # Missing both credentials and instance profile
            use_instance_profile=False,
        )


# Test ValidationResult model
def test_validation_result():
    """Test the ValidationResult model"""
    # Create a successful validation result
    success_result = ValidationResult(
        success=True,
        message="Validation successful",
        details={"connection": "established", "tables": ["users", "products"]},
        warnings=["SSL not enabled"],
    )

    assert success_result.success is True
    assert success_result.message == "Validation successful"
    assert success_result.details["connection"] == "established"
    assert success_result.warnings[0] == "SSL not enabled"

    # Create a failed validation result
    failed_result = ValidationResult(
        success=False,
        message="Validation failed",
        details={"error": "Connection refused"},
        warnings=["Check network settings"],
    )

    assert failed_result.success is False
    assert failed_result.message == "Validation failed"
    assert failed_result.details["error"] == "Connection refused"


# Test DataSourceResponse model
def test_datasource_response():
    """Test the DataSourceResponse model"""
    # Create a data source response
    response = DataSourceResponse(
        id=uuid4(),
        name="Test Database",
        type="postgres",
        description="Test database configuration",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        config={
            "host": "localhost",
            "port": 5432,
            "database": "testdb",
            "username": "testuser",
            "password": "********",
        },
    )

    assert response.name == "Test Database"
    assert response.type == "postgres"
    assert isinstance(response.id, UUID)
    assert isinstance(response.created_at, datetime)
    assert isinstance(response.updated_at, datetime)
    assert response.config["host"] == "localhost"
    assert response.config["port"] == 5432
    assert response.config["password"] == "********"


# Test DataSourceList model
def test_datasource_list():
    """Test the DataSourceList model"""
    # Create a data source list
    datasource_list = DataSourceList(
        datasources=[
            DataSourceResponse(
                id=uuid4(),
                name="Database 1",
                type="postgres",
                description="First database",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                config={"database": "db1"},
            ),
            DataSourceResponse(
                id=uuid4(),
                name="Database 2",
                type="mysql",
                description="Second database",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                config={"database": "db2"},
            ),
        ],
        total=2,
    )

    assert len(datasource_list.datasources) == 2
    assert datasource_list.total == 2
    assert datasource_list.datasources[0].name == "Database 1"
    assert datasource_list.datasources[1].name == "Database 2"


# Test DataSourceTypeInfo model
def test_datasource_type_info():
    """Test the DataSourceTypeInfo model"""
    # Create a data source type info
    type_info = DataSourceTypeInfo(
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

    assert type_info.type == "postgres"
    assert type_info.description == "PostgreSQL database"
    assert len(type_info.parameters) == 3
    assert type_info.parameters[0]["name"] == "host"
    assert type_info.parameters[2]["required"] is True


# Test DataSourceTypeList model
def test_datasource_type_list():
    """Test the DataSourceTypeList model"""
    # Create a data source type list
    type_list = DataSourceTypeList(
        types=[
            DataSourceTypeInfo(
                type="postgres",
                description="PostgreSQL database",
                parameters=[{"name": "database", "type": "string", "required": True}],
            ),
            DataSourceTypeInfo(
                type="mysql",
                description="MySQL database",
                parameters=[{"name": "database", "type": "string", "required": True}],
            ),
        ]
    )

    assert len(type_list.types) == 2
    assert type_list.types[0].type == "postgres"
    assert type_list.types[1].type == "mysql"
