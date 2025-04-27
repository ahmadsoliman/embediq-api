"""
Registry for data source types and extensions.
"""

import logging
import importlib
import pkgutil
import inspect
from typing import Dict, List, Optional, Any, Type, Tuple, Callable
import os

from app.models.datasources import (
    DataSourceConfig,
    DatabaseDataSource,
    FileDataSource,
    APIDataSource,
    S3DataSource,
    DataSourceTypeInfo,
)

logger = logging.getLogger(__name__)


class DataSourceTypeRegistry:
    """Registry for data source types and their validators"""

    # Singleton instance
    _instance = None

    def __new__(cls):
        """Ensure singleton pattern"""
        if cls._instance is None:
            cls._instance = super(DataSourceTypeRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the registry"""
        if self._initialized:
            return

        # Dictionary to store registered types
        self._types: Dict[str, Dict[str, Any]] = {}

        # Register built-in types
        self._register_builtin_types()

        # Flag as initialized
        self._initialized = True

    def _register_builtin_types(self):
        """Register built-in data source types"""
        # PostgreSQL
        self.register_type(
            type_name="postgres",
            model_class=DatabaseDataSource,
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
                {
                    "name": "username",
                    "type": "string",
                    "required": False,
                    "description": "Database username",
                },
                {
                    "name": "password",
                    "type": "string",
                    "required": False,
                    "description": "Database password",
                    "sensitive": True,
                },
                {
                    "name": "connection_string",
                    "type": "string",
                    "required": False,
                    "description": "Database connection string (alternative to individual parameters)",
                    "sensitive": True,
                },
                {
                    "name": "ssl_mode",
                    "type": "string",
                    "required": False,
                    "description": "SSL mode for connection",
                    "enum": ["disable", "allow", "prefer", "require", "verify-ca", "verify-full"],
                },
            ],
        )

        # MySQL
        self.register_type(
            type_name="mysql",
            model_class=DatabaseDataSource,
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
                {
                    "name": "username",
                    "type": "string",
                    "required": False,
                    "description": "Database username",
                },
                {
                    "name": "password",
                    "type": "string",
                    "required": False,
                    "description": "Database password",
                    "sensitive": True,
                },
                {
                    "name": "connection_string",
                    "type": "string",
                    "required": False,
                    "description": "Database connection string (alternative to individual parameters)",
                    "sensitive": True,
                },
            ],
        )

        # SQLite
        self.register_type(
            type_name="sqlite",
            model_class=DatabaseDataSource,
            description="SQLite database",
            parameters=[
                {
                    "name": "database",
                    "type": "string",
                    "required": True,
                    "description": "Database file path",
                },
                {
                    "name": "connection_string",
                    "type": "string",
                    "required": False,
                    "description": "Database connection string (alternative to database parameter)",
                },
            ],
        )

        # CSV
        self.register_type(
            type_name="csv",
            model_class=FileDataSource,
            description="CSV file",
            parameters=[
                {
                    "name": "path",
                    "type": "string",
                    "required": True,
                    "description": "File path",
                },
                {
                    "name": "delimiter",
                    "type": "string",
                    "required": False,
                    "description": "CSV delimiter",
                    "default": ",",
                },
                {
                    "name": "has_header",
                    "type": "boolean",
                    "required": False,
                    "description": "Whether the file has a header row",
                    "default": True,
                },
                {
                    "name": "encoding",
                    "type": "string",
                    "required": False,
                    "description": "File encoding",
                    "default": "utf-8",
                },
            ],
        )

        # JSON
        self.register_type(
            type_name="json",
            model_class=FileDataSource,
            description="JSON file",
            parameters=[
                {
                    "name": "path",
                    "type": "string",
                    "required": True,
                    "description": "File path",
                },
                {
                    "name": "encoding",
                    "type": "string",
                    "required": False,
                    "description": "File encoding",
                    "default": "utf-8",
                },
            ],
        )

        # API
        self.register_type(
            type_name="api",
            model_class=APIDataSource,
            description="REST API",
            parameters=[
                {
                    "name": "url",
                    "type": "string",
                    "required": True,
                    "description": "API endpoint URL",
                },
                {
                    "name": "method",
                    "type": "string",
                    "required": False,
                    "description": "HTTP method",
                    "default": "GET",
                    "enum": ["GET", "POST", "PUT", "DELETE"],
                },
                {
                    "name": "headers",
                    "type": "object",
                    "required": False,
                    "description": "HTTP headers",
                },
                {
                    "name": "auth_type",
                    "type": "string",
                    "required": False,
                    "description": "Authentication type",
                    "enum": ["basic", "bearer", "api_key"],
                },
                {
                    "name": "auth_username",
                    "type": "string",
                    "required": False,
                    "description": "Username for basic auth",
                },
                {
                    "name": "auth_password",
                    "type": "string",
                    "required": False,
                    "description": "Password for basic auth",
                    "sensitive": True,
                },
                {
                    "name": "auth_token",
                    "type": "string",
                    "required": False,
                    "description": "Token for bearer auth",
                    "sensitive": True,
                },
                {
                    "name": "api_key",
                    "type": "string",
                    "required": False,
                    "description": "API key",
                    "sensitive": True,
                },
                {
                    "name": "api_key_name",
                    "type": "string",
                    "required": False,
                    "description": "API key parameter name",
                },
                {
                    "name": "api_key_location",
                    "type": "string",
                    "required": False,
                    "description": "API key location",
                    "default": "header",
                    "enum": ["header", "query"],
                },
                {
                    "name": "request_body",
                    "type": "object",
                    "required": False,
                    "description": "Request body for POST/PUT",
                },
                {
                    "name": "response_format",
                    "type": "string",
                    "required": False,
                    "description": "Expected response format",
                    "default": "json",
                    "enum": ["json", "text", "binary"],
                },
            ],
        )

        # S3
        self.register_type(
            type_name="s3",
            model_class=S3DataSource,
            description="Amazon S3 bucket",
            parameters=[
                {
                    "name": "bucket",
                    "type": "string",
                    "required": True,
                    "description": "S3 bucket name",
                },
                {
                    "name": "prefix",
                    "type": "string",
                    "required": False,
                    "description": "S3 object prefix",
                    "default": "",
                },
                {
                    "name": "region",
                    "type": "string",
                    "required": False,
                    "description": "AWS region",
                    "default": "us-east-1",
                },
                {
                    "name": "access_key",
                    "type": "string",
                    "required": False,
                    "description": "AWS access key",
                },
                {
                    "name": "secret_key",
                    "type": "string",
                    "required": False,
                    "description": "AWS secret key",
                    "sensitive": True,
                },
                {
                    "name": "use_instance_profile",
                    "type": "boolean",
                    "required": False,
                    "description": "Use EC2 instance profile for authentication",
                    "default": False,
                },
                {
                    "name": "file_format",
                    "type": "string",
                    "required": False,
                    "description": "Format of files in the bucket",
                    "enum": ["csv", "json", "parquet", "avro"],
                },
            ],
        )

    def register_type(
        self,
        type_name: str,
        model_class: Type[DataSourceConfig],
        description: str = "",
        parameters: List[Dict[str, Any]] = None,
        validator_func: Optional[Callable] = None,
    ) -> None:
        """
        Register a data source type
        
        Args:
            type_name: The type name
            model_class: The model class for this type
            description: Description of the data source type
            parameters: List of parameter definitions
            validator_func: Optional validator function
        """
        if parameters is None:
            parameters = []

        self._types[type_name] = {
            "model_class": model_class,
            "description": description,
            "parameters": parameters,
            "validator_func": validator_func,
        }

        logger.info(f"Registered data source type: {type_name}")

    def get_type(self, type_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a registered data source type
        
        Args:
            type_name: The type name
            
        Returns:
            The type information, or None if not found
        """
        return self._types.get(type_name)

    def get_model_class(self, type_name: str) -> Optional[Type[DataSourceConfig]]:
        """
        Get the model class for a data source type
        
        Args:
            type_name: The type name
            
        Returns:
            The model class, or None if not found
        """
        type_info = self.get_type(type_name)
        if type_info:
            return type_info["model_class"]
        return None

    def get_validator_func(self, type_name: str) -> Optional[Callable]:
        """
        Get the validator function for a data source type
        
        Args:
            type_name: The type name
            
        Returns:
            The validator function, or None if not found
        """
        type_info = self.get_type(type_name)
        if type_info and "validator_func" in type_info:
            return type_info["validator_func"]
        return None

    def list_types(self) -> List[str]:
        """
        List all registered data source types
        
        Returns:
            A list of type names
        """
        return list(self._types.keys())

    def get_type_info(self, type_name: str) -> Optional[DataSourceTypeInfo]:
        """
        Get information about a data source type
        
        Args:
            type_name: The type name
            
        Returns:
            Type information, or None if not found
        """
        type_info = self.get_type(type_name)
        if not type_info:
            return None

        return DataSourceTypeInfo(
            type=type_name,
            description=type_info["description"],
            parameters=type_info["parameters"],
        )

    def list_type_info(self) -> List[DataSourceTypeInfo]:
        """
        List information about all registered data source types
        
        Returns:
            A list of type information
        """
        return [self.get_type_info(type_name) for type_name in self.list_types()]

    def load_extensions(self, extensions_dir: str = None) -> int:
        """
        Load data source type extensions from a directory
        
        Args:
            extensions_dir: Directory containing extension modules
            
        Returns:
            Number of extensions loaded
        """
        if not extensions_dir:
            # Use default extensions directory
            extensions_dir = os.path.join(os.path.dirname(__file__), "..", "extensions", "datasources")

        if not os.path.isdir(extensions_dir):
            logger.warning(f"Extensions directory not found: {extensions_dir}")
            return 0

        # Add extensions directory to Python path
        import sys
        if extensions_dir not in sys.path:
            sys.path.insert(0, extensions_dir)

        # Find and load extension modules
        extension_count = 0
        for _, name, is_pkg in pkgutil.iter_modules([extensions_dir]):
            if is_pkg:
                continue

            try:
                # Import the module
                module = importlib.import_module(name)

                # Look for DataSourceExtension classes
                for _, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and hasattr(obj, "get_type_name")
                        and hasattr(obj, "get_model_class")
                        and callable(obj.get_type_name)
                        and callable(obj.get_model_class)
                    ):
                        # Create an instance of the extension
                        extension = obj()

                        # Register the type
                        type_name = extension.get_type_name()
                        model_class = extension.get_model_class()
                        description = extension.get_description() if hasattr(extension, "get_description") and callable(extension.get_description) else ""
                        parameters = extension.get_parameters() if hasattr(extension, "get_parameters") and callable(extension.get_parameters) else []
                        validator_func = extension.get_validator_func() if hasattr(extension, "get_validator_func") and callable(extension.get_validator_func) else None

                        self.register_type(
                            type_name=type_name,
                            model_class=model_class,
                            description=description,
                            parameters=parameters,
                            validator_func=validator_func,
                        )

                        extension_count += 1
                        logger.info(f"Loaded data source extension: {type_name} from {name}")
            except Exception as e:
                logger.error(f"Error loading extension module {name}: {str(e)}")

        return extension_count


# Create a singleton instance
datasource_registry = DataSourceTypeRegistry()
