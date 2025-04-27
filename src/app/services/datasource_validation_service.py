"""
Service for validating data source configurations.
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional, Union
import httpx
import csv
import json
import sqlite3
from contextlib import asynccontextmanager

from app.models.datasources import (
    DataSourceConfig,
    DatabaseDataSource,
    FileDataSource,
    APIDataSource,
    S3DataSource,
    ValidationResult,
)

logger = logging.getLogger(__name__)

# Timeout for validation operations (in seconds)
VALIDATION_TIMEOUT = 10


class DataSourceValidationService:
    """Service for validating data source configurations"""

    @staticmethod
    async def validate_config(config: DataSourceConfig) -> ValidationResult:
        """
        Validate a data source configuration
        
        Args:
            config: The data source configuration to validate
            
        Returns:
            A validation result
        """
        try:
            # Validate based on data source type
            if isinstance(config, DatabaseDataSource):
                return await DataSourceValidationService.validate_database_connection(config)
            elif isinstance(config, FileDataSource):
                return await DataSourceValidationService.validate_file_access(config)
            elif isinstance(config, APIDataSource):
                return await DataSourceValidationService.validate_api_endpoint(config)
            elif isinstance(config, S3DataSource):
                return await DataSourceValidationService.validate_s3_access(config)
            else:
                return ValidationResult(
                    success=False,
                    message=f"Unsupported data source type: {config.type}",
                    details={"type": config.type},
                )
        except Exception as e:
            logger.error(f"Error validating data source: {str(e)}")
            return ValidationResult(
                success=False,
                message=f"Validation error: {str(e)}",
                details={"error": str(e)},
            )

    @staticmethod
    async def validate_database_connection(config: DatabaseDataSource) -> ValidationResult:
        """
        Validate a database connection
        
        Args:
            config: The database configuration to validate
            
        Returns:
            A validation result
        """
        warnings = []
        details = {"database_type": config.type}
        
        try:
            # Use asyncio.wait_for to implement timeout
            result = await asyncio.wait_for(
                DataSourceValidationService._validate_db_connection(config),
                timeout=VALIDATION_TIMEOUT
            )
            
            # Add any warnings from the validation
            if "warnings" in result:
                warnings.extend(result["warnings"])
                
            # Add details from the validation
            if "details" in result:
                details.update(result["details"])
                
            return ValidationResult(
                success=result["success"],
                message=result["message"],
                details=details,
                warnings=warnings,
            )
        except asyncio.TimeoutError:
            return ValidationResult(
                success=False,
                message="Database connection validation timed out",
                details=details,
                warnings=warnings,
            )
        except Exception as e:
            logger.error(f"Error validating database connection: {str(e)}")
            return ValidationResult(
                success=False,
                message=f"Database connection error: {str(e)}",
                details=details,
                warnings=warnings,
            )

    @staticmethod
    async def _validate_db_connection(config: DatabaseDataSource) -> Dict[str, Any]:
        """
        Internal method to validate database connection
        
        Args:
            config: The database configuration
            
        Returns:
            A dictionary with validation results
        """
        # SQLite validation is handled differently
        if config.type == "sqlite":
            return await DataSourceValidationService._validate_sqlite_connection(config)
            
        # For PostgreSQL and MySQL, we need to import the appropriate libraries
        # We import them here to avoid unnecessary dependencies if not used
        if config.type == "postgres":
            try:
                import psycopg2
                from psycopg2 import sql
            except ImportError:
                return {
                    "success": False,
                    "message": "PostgreSQL driver (psycopg2) not installed",
                    "warnings": ["Install psycopg2 to validate PostgreSQL connections"],
                }
                
            # Construct connection parameters
            if config.connection_string:
                conn_string = config.connection_string
            else:
                # Build connection string from components
                conn_string = f"postgresql://"
                if config.username:
                    conn_string += f"{config.username}"
                    if hasattr(config.password, "get_secret_value"):
                        conn_string += f":{config.password.get_secret_value()}"
                    elif config.password:
                        conn_string += f":{config.password}"
                conn_string += f"@{config.host or 'localhost'}"
                if config.port:
                    conn_string += f":{config.port}"
                conn_string += f"/{config.database}"
                
            try:
                # Connect to the database
                conn = psycopg2.connect(conn_string)
                cursor = conn.cursor()
                
                # Test a simple query
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
                # Check if we got the expected result
                if result and result[0] == 1:
                    # Test table listing to check permissions
                    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                    tables = cursor.fetchall()
                    
                    conn.close()
                    return {
                        "success": True,
                        "message": "Successfully connected to PostgreSQL database",
                        "details": {
                            "tables_count": len(tables),
                            "tables": [table[0] for table in tables[:5]],  # Show first 5 tables
                        },
                    }
                else:
                    conn.close()
                    return {
                        "success": False,
                        "message": "Connected to PostgreSQL database but test query failed",
                    }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"PostgreSQL connection error: {str(e)}",
                }
                
        elif config.type == "mysql":
            try:
                import mysql.connector
            except ImportError:
                return {
                    "success": False,
                    "message": "MySQL driver (mysql-connector-python) not installed",
                    "warnings": ["Install mysql-connector-python to validate MySQL connections"],
                }
                
            try:
                # Construct connection parameters
                if config.connection_string:
                    # Parse connection string to get parameters
                    # This is a simplified version and might not handle all connection string formats
                    conn_params = {}
                    conn_string = config.connection_string.replace("mysql://", "")
                    
                    # Extract username:password@host:port/database
                    auth_db_parts = conn_string.split("@")
                    if len(auth_db_parts) > 1:
                        auth = auth_db_parts[0]
                        host_db = auth_db_parts[1]
                        
                        # Extract username and password
                        if ":" in auth:
                            username, password = auth.split(":", 1)
                            conn_params["user"] = username
                            conn_params["password"] = password
                        else:
                            conn_params["user"] = auth
                            
                        # Extract host, port, and database
                        if "/" in host_db:
                            host_port, database = host_db.split("/", 1)
                            conn_params["database"] = database
                            
                            if ":" in host_port:
                                host, port = host_port.split(":", 1)
                                conn_params["host"] = host
                                conn_params["port"] = int(port)
                            else:
                                conn_params["host"] = host_port
                    else:
                        # Simple case: just a database name
                        conn_params["database"] = conn_string
                else:
                    # Use individual parameters
                    conn_params = {
                        "host": config.host or "localhost",
                        "database": config.database,
                    }
                    
                    if config.port:
                        conn_params["port"] = config.port
                        
                    if config.username:
                        conn_params["user"] = config.username
                        
                    if config.password:
                        if hasattr(config.password, "get_secret_value"):
                            conn_params["password"] = config.password.get_secret_value()
                        else:
                            conn_params["password"] = config.password
                
                # Connect to the database
                conn = mysql.connector.connect(**conn_params)
                cursor = conn.cursor()
                
                # Test a simple query
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
                # Check if we got the expected result
                if result and result[0] == 1:
                    # Test table listing to check permissions
                    cursor.execute("SHOW TABLES")
                    tables = cursor.fetchall()
                    
                    conn.close()
                    return {
                        "success": True,
                        "message": "Successfully connected to MySQL database",
                        "details": {
                            "tables_count": len(tables),
                            "tables": [table[0] for table in tables[:5]],  # Show first 5 tables
                        },
                    }
                else:
                    conn.close()
                    return {
                        "success": False,
                        "message": "Connected to MySQL database but test query failed",
                    }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"MySQL connection error: {str(e)}",
                }
        
        # Unsupported database type
        return {
            "success": False,
            "message": f"Unsupported database type: {config.type}",
        }

    @staticmethod
    async def _validate_sqlite_connection(config: DatabaseDataSource) -> Dict[str, Any]:
        """
        Validate SQLite connection
        
        Args:
            config: The SQLite configuration
            
        Returns:
            A dictionary with validation results
        """
        try:
            # Determine the database path
            if config.connection_string:
                # Extract path from connection string
                db_path = config.connection_string.replace("sqlite:///", "")
            else:
                db_path = config.database
                
            # Check if the file exists
            if not os.path.isfile(db_path):
                return {
                    "success": False,
                    "message": f"SQLite database file not found: {db_path}",
                }
                
            # Check if the file is readable
            if not os.access(db_path, os.R_OK):
                return {
                    "success": False,
                    "message": f"SQLite database file is not readable: {db_path}",
                }
                
            # Try to connect to the database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Test a simple query
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            # Check if we got the expected result
            if result and result[0] == 1:
                # Get table list
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                conn.close()
                return {
                    "success": True,
                    "message": "Successfully connected to SQLite database",
                    "details": {
                        "tables_count": len(tables),
                        "tables": [table[0] for table in tables[:5]],  # Show first 5 tables
                    },
                }
            else:
                conn.close()
                return {
                    "success": False,
                    "message": "Connected to SQLite database but test query failed",
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"SQLite connection error: {str(e)}",
            }

    @staticmethod
    async def validate_file_access(config: FileDataSource) -> ValidationResult:
        """
        Validate file access
        
        Args:
            config: The file configuration to validate
            
        Returns:
            A validation result
        """
        warnings = []
        details = {"file_type": config.type}
        
        try:
            # Check if the file exists
            if not os.path.isfile(config.path):
                return ValidationResult(
                    success=False,
                    message=f"File not found: {config.path}",
                    details=details,
                    warnings=warnings,
                )
                
            # Check if the file is readable
            if not os.access(config.path, os.R_OK):
                return ValidationResult(
                    success=False,
                    message=f"File is not readable: {config.path}",
                    details=details,
                    warnings=warnings,
                )
                
            # Validate based on file type
            if config.type == "csv":
                # Try to read the CSV file
                with open(config.path, "r", encoding=config.encoding) as f:
                    # Read the first few lines
                    reader = csv.reader(f, delimiter=config.delimiter)
                    
                    # Get header if available
                    header = next(reader) if config.has_header else None
                    
                    # Read a few rows
                    rows = []
                    for i, row in enumerate(reader):
                        if i >= 5:  # Read up to 5 rows
                            break
                        rows.append(row)
                        
                    details["header"] = header
                    details["sample_rows"] = rows
                    details["row_count"] = i + 1
                    
                    return ValidationResult(
                        success=True,
                        message=f"Successfully validated CSV file with {i + 1} rows",
                        details=details,
                        warnings=warnings,
                    )
            elif config.type == "json":
                # Try to parse the JSON file
                with open(config.path, "r", encoding=config.encoding) as f:
                    data = json.load(f)
                    
                    # Determine the structure
                    if isinstance(data, list):
                        details["structure"] = "array"
                        details["items_count"] = len(data)
                        details["sample_item"] = data[0] if data else None
                    elif isinstance(data, dict):
                        details["structure"] = "object"
                        details["keys"] = list(data.keys())
                        
                    return ValidationResult(
                        success=True,
                        message="Successfully validated JSON file",
                        details=details,
                        warnings=warnings,
                    )
            else:
                # For other file types, just check if it's readable
                return ValidationResult(
                    success=True,
                    message=f"File exists and is readable: {config.path}",
                    details=details,
                    warnings=["File content validation not implemented for this type"],
                )
        except Exception as e:
            logger.error(f"Error validating file access: {str(e)}")
            return ValidationResult(
                success=False,
                message=f"File validation error: {str(e)}",
                details=details,
                warnings=warnings,
            )

    @staticmethod
    async def validate_api_endpoint(config: APIDataSource) -> ValidationResult:
        """
        Validate an API endpoint
        
        Args:
            config: The API configuration to validate
            
        Returns:
            A validation result
        """
        warnings = []
        details = {"method": config.method, "url": config.url}
        
        try:
            # Use asyncio.wait_for to implement timeout
            result = await asyncio.wait_for(
                DataSourceValidationService._validate_api_request(config),
                timeout=VALIDATION_TIMEOUT
            )
            
            # Add any warnings from the validation
            if "warnings" in result:
                warnings.extend(result["warnings"])
                
            # Add details from the validation
            if "details" in result:
                details.update(result["details"])
                
            return ValidationResult(
                success=result["success"],
                message=result["message"],
                details=details,
                warnings=warnings,
            )
        except asyncio.TimeoutError:
            return ValidationResult(
                success=False,
                message="API request validation timed out",
                details=details,
                warnings=warnings,
            )
        except Exception as e:
            logger.error(f"Error validating API endpoint: {str(e)}")
            return ValidationResult(
                success=False,
                message=f"API validation error: {str(e)}",
                details=details,
                warnings=warnings,
            )

    @staticmethod
    async def _validate_api_request(config: APIDataSource) -> Dict[str, Any]:
        """
        Internal method to validate API request
        
        Args:
            config: The API configuration
            
        Returns:
            A dictionary with validation results
        """
        # Prepare headers
        headers = config.headers.copy() if config.headers else {}
        
        # Add authentication headers if needed
        if config.auth_type == "basic":
            if config.auth_username and config.auth_password:
                import base64
                
                # Get password value
                password = config.auth_password
                if hasattr(password, "get_secret_value"):
                    password = password.get_secret_value()
                    
                # Create basic auth header
                auth_string = f"{config.auth_username}:{password}"
                encoded_auth = base64.b64encode(auth_string.encode()).decode()
                headers["Authorization"] = f"Basic {encoded_auth}"
        elif config.auth_type == "bearer":
            if config.auth_token:
                # Get token value
                token = config.auth_token
                if hasattr(token, "get_secret_value"):
                    token = token.get_secret_value()
                    
                headers["Authorization"] = f"Bearer {token}"
        elif config.auth_type == "api_key":
            if config.api_key and config.api_key_name:
                # Get API key value
                api_key = config.api_key
                if hasattr(api_key, "get_secret_value"):
                    api_key = api_key.get_secret_value()
                    
                if config.api_key_location == "header":
                    headers[config.api_key_name] = api_key
                    
        # Prepare request parameters
        request_params = {}
        
        # Add API key to query parameters if needed
        if config.auth_type == "api_key" and config.api_key_location == "query":
            api_key = config.api_key
            if hasattr(api_key, "get_secret_value"):
                api_key = api_key.get_secret_value()
                
            request_params[config.api_key_name] = api_key
            
        # Make the request
        async with httpx.AsyncClient() as client:
            try:
                if config.method.upper() == "GET":
                    response = await client.get(
                        config.url,
                        headers=headers,
                        params=request_params,
                        follow_redirects=True,
                    )
                elif config.method.upper() == "POST":
                    response = await client.post(
                        config.url,
                        headers=headers,
                        params=request_params,
                        json=config.request_body,
                        follow_redirects=True,
                    )
                else:
                    return {
                        "success": False,
                        "message": f"Unsupported HTTP method: {config.method}",
                        "warnings": ["Only GET and POST methods are supported for validation"],
                    }
                    
                # Check response status
                if response.status_code < 400:
                    # Try to parse response based on expected format
                    response_details = {}
                    
                    if config.response_format == "json":
                        try:
                            response_data = response.json()
                            response_details["response_type"] = "json"
                            
                            # Add sample of response data
                            if isinstance(response_data, dict):
                                response_details["keys"] = list(response_data.keys())
                            elif isinstance(response_data, list):
                                response_details["items_count"] = len(response_data)
                                if response_data:
                                    response_details["first_item_keys"] = list(response_data[0].keys()) if isinstance(response_data[0], dict) else "non-object"
                        except Exception as e:
                            return {
                                "success": False,
                                "message": f"API returned status {response.status_code} but response is not valid JSON",
                                "details": {"status_code": response.status_code},
                                "warnings": [f"JSON parsing error: {str(e)}"],
                            }
                    else:
                        # For other formats, just check content length
                        response_details["content_length"] = len(response.content)
                        
                    return {
                        "success": True,
                        "message": f"API request successful with status {response.status_code}",
                        "details": {
                            "status_code": response.status_code,
                            "content_type": response.headers.get("content-type"),
                            **response_details,
                        },
                    }
                else:
                    return {
                        "success": False,
                        "message": f"API request failed with status {response.status_code}",
                        "details": {"status_code": response.status_code},
                    }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"API request error: {str(e)}",
                }

    @staticmethod
    async def validate_s3_access(config: S3DataSource) -> ValidationResult:
        """
        Validate S3 access
        
        Args:
            config: The S3 configuration to validate
            
        Returns:
            A validation result
        """
        warnings = []
        details = {"bucket": config.bucket, "region": config.region}
        
        try:
            # Try to import boto3
            try:
                import boto3
                from botocore.exceptions import ClientError
            except ImportError:
                return ValidationResult(
                    success=False,
                    message="AWS SDK (boto3) not installed",
                    details=details,
                    warnings=["Install boto3 to validate S3 connections"],
                )
                
            # Create S3 client
            s3_kwargs = {"region_name": config.region}
            
            if not config.use_instance_profile:
                # Use provided credentials
                if config.access_key and config.secret_key:
                    # Get secret key value
                    secret_key = config.secret_key
                    if hasattr(secret_key, "get_secret_value"):
                        secret_key = secret_key.get_secret_value()
                        
                    s3_kwargs["aws_access_key_id"] = config.access_key
                    s3_kwargs["aws_secret_access_key"] = secret_key
                else:
                    warnings.append("No credentials provided, using default AWS credential chain")
                    
            # Create S3 client
            s3 = boto3.client("s3", **s3_kwargs)
            
            # Check if bucket exists and is accessible
            try:
                # List objects with prefix to check access
                response = s3.list_objects_v2(
                    Bucket=config.bucket,
                    Prefix=config.prefix,
                    MaxKeys=5,
                )
                
                # Get object count
                object_count = response.get("KeyCount", 0)
                
                # Get sample objects
                objects = []
                if "Contents" in response:
                    for obj in response["Contents"]:
                        objects.append(obj["Key"])
                        
                return ValidationResult(
                    success=True,
                    message=f"Successfully accessed S3 bucket with {object_count} objects",
                    details={
                        **details,
                        "object_count": object_count,
                        "sample_objects": objects,
                    },
                    warnings=warnings,
                )
            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                error_message = e.response["Error"]["Message"]
                
                return ValidationResult(
                    success=False,
                    message=f"S3 access error: {error_code} - {error_message}",
                    details={**details, "error_code": error_code},
                    warnings=warnings,
                )
        except Exception as e:
            logger.error(f"Error validating S3 access: {str(e)}")
            return ValidationResult(
                success=False,
                message=f"S3 validation error: {str(e)}",
                details=details,
                warnings=warnings,
            )
