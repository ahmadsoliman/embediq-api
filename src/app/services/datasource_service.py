"""
Service for managing data source configurations.
"""

import os
import json
import logging
import shutil
from typing import Dict, List, Optional, Any, Union
from uuid import uuid4
from datetime import datetime, timezone
import fcntl
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from app.config import DATA_DIR
from app.models.datasources import (
    DataSourceConfig,
    DatabaseDataSource,
    FileDataSource,
    APIDataSource,
    S3DataSource,
    ValidationResult,
)
from app.utilities.helpers import ensure_user_dir

logger = logging.getLogger(__name__)

# Salt for encryption key derivation
ENCRYPTION_SALT = b"embediq-datasource-config-salt"


class ConfigurationStorageService:
    """Service for managing data source configurations"""

    @staticmethod
    def get_user_datasources_dir(user_id: str) -> str:
        """
        Get the user's data sources directory

        Args:
            user_id: The user ID

        Returns:
            The path to the user's data sources directory
        """
        # Ensure base data directory exists
        os.makedirs(DATA_DIR, exist_ok=True)

        # Ensure user directory exists
        user_dir = ensure_user_dir(DATA_DIR, user_id)

        # Ensure datasources directory exists
        datasources_dir = os.path.join(user_dir, "datasources")
        os.makedirs(datasources_dir, exist_ok=True)

        return datasources_dir

    @staticmethod
    def _get_encryption_key(user_id: str) -> bytes:
        """
        Derive an encryption key from the user ID

        Args:
            user_id: The user ID

        Returns:
            The encryption key
        """
        # Use PBKDF2 to derive a key from the user ID
        # In a production environment, this should use a secure secret from environment variables
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=ENCRYPTION_SALT,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(user_id.encode()))
        return key

    @staticmethod
    def _encrypt_sensitive_data(data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Encrypt sensitive data in the configuration

        Args:
            data: The configuration data
            user_id: The user ID

        Returns:
            The configuration with encrypted sensitive data
        """
        # Create a copy to avoid modifying the original
        encrypted_data = data.copy()

        # Get encryption key
        key = ConfigurationStorageService._get_encryption_key(user_id)
        fernet = Fernet(key)

        # Fields to encrypt based on data source type
        sensitive_fields = []

        if data.get("type") in ["postgres", "mysql", "sqlite"]:
            sensitive_fields = ["password", "connection_string"]
        elif data.get("type") == "api":
            sensitive_fields = ["auth_password", "auth_token", "api_key"]
        elif data.get("type") == "s3":
            sensitive_fields = ["secret_key"]

        # Encrypt sensitive fields if they exist and are not already encrypted
        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field]:
                # Skip if the field is already a string and looks encrypted
                if isinstance(encrypted_data[field], str) and encrypted_data[
                    field
                ].startswith("gAAAAA"):
                    continue

                # Encrypt the field
                try:
                    value = encrypted_data[field]
                    # Handle SecretStr from Pydantic models
                    if hasattr(value, "get_secret_value"):
                        value = value.get_secret_value()
                    encrypted_value = fernet.encrypt(str(value).encode()).decode()
                    encrypted_data[field] = encrypted_value
                except Exception as e:
                    logger.error(f"Error encrypting field {field}: {str(e)}")

        return encrypted_data

    @staticmethod
    def _decrypt_sensitive_data(data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Decrypt sensitive data in the configuration

        Args:
            data: The configuration data
            user_id: The user ID

        Returns:
            The configuration with decrypted sensitive data
        """
        # Create a copy to avoid modifying the original
        decrypted_data = data.copy()

        # Get encryption key
        key = ConfigurationStorageService._get_encryption_key(user_id)
        fernet = Fernet(key)

        # Fields to decrypt based on data source type
        sensitive_fields = []

        if data.get("type") in ["postgres", "mysql", "sqlite"]:
            sensitive_fields = ["password", "connection_string"]
        elif data.get("type") == "api":
            sensitive_fields = ["auth_password", "auth_token", "api_key"]
        elif data.get("type") == "s3":
            sensitive_fields = ["secret_key"]

        # Decrypt sensitive fields if they exist and look encrypted
        for field in sensitive_fields:
            if field in decrypted_data and decrypted_data[field]:
                # Only decrypt if the field is a string and looks encrypted
                if isinstance(decrypted_data[field], str) and decrypted_data[
                    field
                ].startswith("gAAAAA"):
                    try:
                        decrypted_value = fernet.decrypt(
                            decrypted_data[field].encode()
                        ).decode()
                        decrypted_data[field] = decrypted_value
                    except Exception as e:
                        logger.error(f"Error decrypting field {field}: {str(e)}")

        return decrypted_data

    @staticmethod
    async def save_config(
        user_id: str, config: Union[DataSourceConfig, Dict[str, Any]]
    ) -> DataSourceConfig:
        """
        Save a data source configuration

        Args:
            user_id: The user ID
            config: The data source configuration

        Returns:
            The saved data source configuration
        """
        # Convert to dict if it's a model
        if isinstance(config, DataSourceConfig):
            config_dict = config.to_dict()
        else:
            config_dict = config

        # Ensure ID exists
        if "id" not in config_dict or not config_dict["id"]:
            config_dict["id"] = str(uuid4())

        # Update timestamps
        now = datetime.now(timezone.utc).isoformat()
        config_dict["updated_at"] = now
        if "created_at" not in config_dict or not config_dict["created_at"]:
            config_dict["created_at"] = now

        # Get the data sources directory
        datasources_dir = ConfigurationStorageService.get_user_datasources_dir(user_id)

        # Create the file path
        file_path = os.path.join(datasources_dir, f"{config_dict['id']}.json")

        # Encrypt sensitive data
        encrypted_config = ConfigurationStorageService._encrypt_sensitive_data(
            config_dict, user_id
        )

        # Save the configuration with file locking
        try:
            with open(file_path, "w") as f:
                # Acquire an exclusive lock
                fcntl.flock(f, fcntl.LOCK_EX)

                # Write the configuration
                json.dump(encrypted_config, f, indent=2)

                # Release the lock
                fcntl.flock(f, fcntl.LOCK_UN)

            logger.info(
                f"Saved data source configuration {config_dict['id']} for user {user_id}"
            )

            # Return the configuration as a model
            return DataSourceConfig.from_dict(config_dict)
        except Exception as e:
            logger.error(f"Error saving data source configuration: {str(e)}")
            raise

    @staticmethod
    async def get_config(user_id: str, config_id: str) -> Optional[DataSourceConfig]:
        """
        Get a data source configuration

        Args:
            user_id: The user ID
            config_id: The configuration ID

        Returns:
            The data source configuration, or None if not found
        """
        # Get the data sources directory
        datasources_dir = ConfigurationStorageService.get_user_datasources_dir(user_id)

        # Create the file path
        file_path = os.path.join(datasources_dir, f"{config_id}.json")

        # Check if the file exists
        if not os.path.isfile(file_path):
            logger.warning(
                f"Data source configuration {config_id} not found for user {user_id}"
            )
            return None

        # Load the configuration with file locking
        try:
            with open(file_path, "r") as f:
                # Acquire a shared lock
                fcntl.flock(f, fcntl.LOCK_SH)

                # Read the configuration
                encrypted_config = json.load(f)

                # Release the lock
                fcntl.flock(f, fcntl.LOCK_UN)

            # Decrypt sensitive data
            config_dict = ConfigurationStorageService._decrypt_sensitive_data(
                encrypted_config, user_id
            )

            logger.info(
                f"Retrieved data source configuration {config_id} for user {user_id}"
            )

            # Return the configuration as a model
            return DataSourceConfig.from_dict(config_dict)
        except Exception as e:
            logger.error(f"Error retrieving data source configuration: {str(e)}")
            raise

    @staticmethod
    async def list_configs(user_id: str) -> List[DataSourceConfig]:
        """
        List all data source configurations for a user

        Args:
            user_id: The user ID

        Returns:
            A list of data source configurations
        """
        # Get the data sources directory
        datasources_dir = ConfigurationStorageService.get_user_datasources_dir(user_id)

        # Get all JSON files in the directory
        config_files = [f for f in os.listdir(datasources_dir) if f.endswith(".json")]

        # Load each configuration
        configs = []
        for file_name in config_files:
            try:
                config_id = file_name.replace(".json", "")
                config = await ConfigurationStorageService.get_config(
                    user_id, config_id
                )
                if config:
                    configs.append(config)
            except Exception as e:
                logger.error(f"Error loading configuration {file_name}: {str(e)}")

        logger.info(
            f"Retrieved {len(configs)} data source configurations for user {user_id}"
        )
        return configs

    @staticmethod
    async def update_config(
        user_id: str, config_id: str, config: Union[DataSourceConfig, Dict[str, Any]]
    ) -> Optional[DataSourceConfig]:
        """
        Update a data source configuration

        Args:
            user_id: The user ID
            config_id: The configuration ID
            config: The updated configuration

        Returns:
            The updated configuration, or None if not found
        """
        # Check if the configuration exists
        existing_config = await ConfigurationStorageService.get_config(
            user_id, config_id
        )
        if not existing_config:
            logger.warning(
                f"Data source configuration {config_id} not found for user {user_id}"
            )
            return None

        # Convert to dict if it's a model
        if isinstance(config, DataSourceConfig):
            config_dict = config.to_dict()
        else:
            config_dict = config

        # Ensure ID matches
        config_dict["id"] = config_id

        # Preserve creation timestamp
        if hasattr(existing_config, "created_at"):
            config_dict["created_at"] = existing_config.created_at.isoformat()

        # Save the updated configuration
        return await ConfigurationStorageService.save_config(user_id, config_dict)

    @staticmethod
    async def delete_config(user_id: str, config_id: str) -> bool:
        """
        Delete a data source configuration

        Args:
            user_id: The user ID
            config_id: The configuration ID

        Returns:
            True if the configuration was deleted, False otherwise
        """
        # Get the data sources directory
        datasources_dir = ConfigurationStorageService.get_user_datasources_dir(user_id)

        # Create the file path
        file_path = os.path.join(datasources_dir, f"{config_id}.json")

        # Check if the file exists
        if not os.path.isfile(file_path):
            logger.warning(
                f"Data source configuration {config_id} not found for user {user_id}"
            )
            return False

        # Delete the file
        try:
            os.remove(file_path)
            logger.info(
                f"Deleted data source configuration {config_id} for user {user_id}"
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting data source configuration: {str(e)}")
            raise
