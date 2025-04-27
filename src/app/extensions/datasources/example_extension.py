"""
Example data source extension for EmbedIQ.

This module demonstrates how to create a custom data source type extension.
"""

from typing import Dict, List, Any, Optional, Type, Callable
from pydantic import BaseModel, Field, SecretStr, validator
from app.models.datasources import DataSourceConfig, ValidationResult


class ElasticsearchDataSource(DataSourceConfig):
    """Model for Elasticsearch data sources"""

    type: str = Field("elasticsearch", description="Elasticsearch data source")
    hosts: List[str] = Field(..., description="Elasticsearch hosts")
    index: str = Field(..., description="Elasticsearch index")
    username: Optional[str] = Field(None, description="Elasticsearch username")
    password: Optional[SecretStr] = Field(None, description="Elasticsearch password")
    api_key: Optional[SecretStr] = Field(None, description="Elasticsearch API key")
    cloud_id: Optional[str] = Field(None, description="Elasticsearch Cloud ID")
    query: Optional[Dict[str, Any]] = Field(None, description="Elasticsearch query")
    ssl_verify: Optional[bool] = Field(True, description="Verify SSL certificates")


class ElasticsearchExtension:
    """Elasticsearch data source extension"""

    def get_type_name(self) -> str:
        """Get the data source type name"""
        return "elasticsearch"

    def get_model_class(self) -> Type[DataSourceConfig]:
        """Get the model class for this data source type"""
        return ElasticsearchDataSource

    def get_description(self) -> str:
        """Get the description of this data source type"""
        return "Elasticsearch database"

    def get_parameters(self) -> List[Dict[str, Any]]:
        """Get the parameters for this data source type"""
        return [
            {
                "name": "hosts",
                "type": "array",
                "required": True,
                "description": "Elasticsearch hosts",
            },
            {
                "name": "index",
                "type": "string",
                "required": True,
                "description": "Elasticsearch index",
            },
            {
                "name": "username",
                "type": "string",
                "required": False,
                "description": "Elasticsearch username",
            },
            {
                "name": "password",
                "type": "string",
                "required": False,
                "description": "Elasticsearch password",
                "sensitive": True,
            },
            {
                "name": "api_key",
                "type": "string",
                "required": False,
                "description": "Elasticsearch API key",
                "sensitive": True,
            },
            {
                "name": "cloud_id",
                "type": "string",
                "required": False,
                "description": "Elasticsearch Cloud ID",
            },
            {
                "name": "query",
                "type": "object",
                "required": False,
                "description": "Elasticsearch query",
            },
            {
                "name": "ssl_verify",
                "type": "boolean",
                "required": False,
                "description": "Verify SSL certificates",
                "default": True,
            },
        ]

    async def validate_elasticsearch(self, config: ElasticsearchDataSource) -> ValidationResult:
        """
        Validate an Elasticsearch connection
        
        Args:
            config: The Elasticsearch configuration
            
        Returns:
            A validation result
        """
        try:
            # Try to import elasticsearch
            try:
                from elasticsearch import Elasticsearch
            except ImportError:
                return ValidationResult(
                    success=False,
                    message="Elasticsearch client not installed",
                    warnings=["Install elasticsearch-py to validate Elasticsearch connections"],
                )
                
            # Create client options
            options = {}
            
            # Add authentication
            if config.username and config.password:
                # Get password value
                password = config.password
                if hasattr(password, "get_secret_value"):
                    password = password.get_secret_value()
                    
                options["basic_auth"] = (config.username, password)
            elif config.api_key:
                # Get API key value
                api_key = config.api_key
                if hasattr(api_key, "get_secret_value"):
                    api_key = api_key.get_secret_value()
                    
                options["api_key"] = api_key
                
            # Add cloud ID if provided
            if config.cloud_id:
                options["cloud_id"] = config.cloud_id
                
            # Add SSL verification
            options["verify_certs"] = config.ssl_verify
            
            # Create client
            es = Elasticsearch(config.hosts, **options)
            
            # Check if the index exists
            if not es.indices.exists(index=config.index):
                return ValidationResult(
                    success=False,
                    message=f"Index {config.index} does not exist",
                )
                
            # Get index stats
            stats = es.indices.stats(index=config.index)
            
            # Get document count
            doc_count = stats["indices"][config.index]["total"]["docs"]["count"]
            
            # Test a simple query
            if config.query:
                # Use provided query
                search_query = config.query
            else:
                # Use a simple match_all query
                search_query = {"query": {"match_all": {}}}
                
            # Execute the query
            search_result = es.search(index=config.index, body=search_query, size=5)
            
            # Get hit count
            hit_count = search_result["hits"]["total"]["value"]
            
            return ValidationResult(
                success=True,
                message=f"Successfully connected to Elasticsearch index with {doc_count} documents",
                details={
                    "index": config.index,
                    "document_count": doc_count,
                    "search_hits": hit_count,
                },
            )
        except Exception as e:
            return ValidationResult(
                success=False,
                message=f"Elasticsearch connection error: {str(e)}",
            )

    def get_validator_func(self) -> Callable:
        """Get the validator function for this data source type"""
        return self.validate_elasticsearch
