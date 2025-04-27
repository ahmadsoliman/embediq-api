# Data Source Configuration API

## Overview

The Data Source Configuration API provides a secure and flexible way to manage external data source configurations in the EmbedIQ platform. This API allows users to create, retrieve, update, delete, and validate various types of data sources, including databases, files, APIs, and cloud storage.

## Features

- **Multiple Data Source Types**: Support for various data source types including:
  - Relational databases (PostgreSQL, MySQL, SQLite)
  - File-based sources (CSV, JSON)
  - REST APIs
  - Cloud storage (Amazon S3)
  
- **Secure Storage**: 
  - Sensitive information (passwords, tokens, keys) is encrypted at rest
  - User-specific storage with proper isolation
  
- **Validation**: 
  - Built-in validation for each data source type
  - Connection testing for databases
  - Endpoint validation for APIs
  - File access verification
  
- **Extensibility**:
  - Registry system for data source types
  - Support for custom data source type extensions

## API Endpoints

### Data Source Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/datasources` | Create a new data source configuration |
| `GET` | `/api/v1/datasources` | List all data source configurations |
| `GET` | `/api/v1/datasources/{id}` | Get a specific data source configuration |
| `PUT` | `/api/v1/datasources/{id}` | Update a data source configuration |
| `DELETE` | `/api/v1/datasources/{id}` | Delete a data source configuration |
| `POST` | `/api/v1/datasources/{id}/validate` | Validate a data source configuration |

### Data Source Type Information

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/datasources/types` | List all supported data source types |
| `GET` | `/api/v1/datasources/types/{type_name}` | Get information about a specific type |

## Authentication

All API endpoints require authentication using a JWT token. The token should be included in the `Authorization` header with the `Bearer` prefix:

```
Authorization: Bearer <your_token>
```

## Data Models

### Base Data Source Configuration

```json
{
  "id": "uuid-string",
  "name": "Data Source Name",
  "type": "postgres|mysql|sqlite|csv|json|api|s3",
  "description": "Optional description",
  "created_at": "2023-04-27T12:34:56.789Z",
  "updated_at": "2023-04-27T12:34:56.789Z"
}
```

### Database Data Source

```json
{
  "id": "uuid-string",
  "name": "PostgreSQL Database",
  "type": "postgres",
  "description": "Production database",
  "host": "db.example.com",
  "port": 5432,
  "database": "mydb",
  "username": "dbuser",
  "password": "********",
  "connection_string": null,
  "ssl_mode": "require",
  "created_at": "2023-04-27T12:34:56.789Z",
  "updated_at": "2023-04-27T12:34:56.789Z"
}
```

### File Data Source

```json
{
  "id": "uuid-string",
  "name": "CSV Data",
  "type": "csv",
  "description": "Customer data file",
  "path": "/path/to/data.csv",
  "delimiter": ",",
  "has_header": true,
  "encoding": "utf-8",
  "created_at": "2023-04-27T12:34:56.789Z",
  "updated_at": "2023-04-27T12:34:56.789Z"
}
```

### API Data Source

```json
{
  "id": "uuid-string",
  "name": "External API",
  "type": "api",
  "description": "Third-party data API",
  "url": "https://api.example.com/data",
  "method": "GET",
  "headers": {
    "Accept": "application/json"
  },
  "auth_type": "bearer",
  "auth_token": "********",
  "response_format": "json",
  "created_at": "2023-04-27T12:34:56.789Z",
  "updated_at": "2023-04-27T12:34:56.789Z"
}
```

### S3 Data Source

```json
{
  "id": "uuid-string",
  "name": "S3 Bucket",
  "type": "s3",
  "description": "Data lake storage",
  "bucket": "my-data-bucket",
  "prefix": "data/",
  "region": "us-west-2",
  "access_key": "AKIAXXXXXXXXXXXXXXXX",
  "secret_key": "********",
  "use_instance_profile": false,
  "file_format": "csv",
  "created_at": "2023-04-27T12:34:56.789Z",
  "updated_at": "2023-04-27T12:34:56.789Z"
}
```

### Validation Result

```json
{
  "success": true,
  "message": "Successfully connected to PostgreSQL database",
  "details": {
    "database_type": "postgres",
    "tables_count": 15,
    "tables": ["users", "products", "orders", "inventory", "categories"]
  },
  "warnings": []
}
```

## Usage Examples

### Creating a Data Source

#### Request

```http
POST /api/v1/datasources
Authorization: Bearer <your_token>
Content-Type: application/json

{
  "name": "Production Database",
  "type": "postgres",
  "description": "Main production database",
  "host": "db.example.com",
  "port": 5432,
  "database": "production",
  "username": "app_user",
  "password": "secure_password",
  "ssl_mode": "require"
}
```

#### Response

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Production Database",
  "type": "postgres",
  "description": "Main production database",
  "created_at": "2023-04-27T12:34:56.789Z",
  "updated_at": "2023-04-27T12:34:56.789Z",
  "config": {
    "host": "db.example.com",
    "port": 5432,
    "database": "production",
    "username": "app_user",
    "password": "********",
    "ssl_mode": "require"
  }
}
```

### Listing Data Sources

#### Request

```http
GET /api/v1/datasources
Authorization: Bearer <your_token>
```

#### Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "datasources": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Production Database",
      "type": "postgres",
      "description": "Main production database",
      "created_at": "2023-04-27T12:34:56.789Z",
      "updated_at": "2023-04-27T12:34:56.789Z",
      "config": {
        "host": "db.example.com",
        "port": 5432,
        "database": "production",
        "username": "app_user",
        "password": "********",
        "ssl_mode": "require"
      }
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Customer Data",
      "type": "csv",
      "description": "Customer data file",
      "created_at": "2023-04-26T10:20:30.456Z",
      "updated_at": "2023-04-26T10:20:30.456Z",
      "config": {
        "path": "/path/to/customers.csv",
        "delimiter": ",",
        "has_header": true,
        "encoding": "utf-8"
      }
    }
  ],
  "total": 2
}
```

### Validating a Data Source

#### Request

```http
POST /api/v1/datasources/550e8400-e29b-41d4-a716-446655440000/validate
Authorization: Bearer <your_token>
```

#### Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "success": true,
  "message": "Successfully connected to PostgreSQL database",
  "details": {
    "database_type": "postgres",
    "tables_count": 15,
    "tables": ["users", "products", "orders", "inventory", "categories"]
  },
  "warnings": []
}
```

### Getting Data Source Type Information

#### Request

```http
GET /api/v1/datasources/types/postgres
Authorization: Bearer <your_token>
```

#### Response

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "type": "postgres",
  "description": "PostgreSQL database",
  "parameters": [
    {
      "name": "host",
      "type": "string",
      "required": false,
      "description": "Database host",
      "default": "localhost"
    },
    {
      "name": "port",
      "type": "integer",
      "required": false,
      "description": "Database port",
      "default": 5432
    },
    {
      "name": "database",
      "type": "string",
      "required": true,
      "description": "Database name"
    },
    {
      "name": "username",
      "type": "string",
      "required": false,
      "description": "Database username"
    },
    {
      "name": "password",
      "type": "string",
      "required": false,
      "description": "Database password",
      "sensitive": true
    },
    {
      "name": "connection_string",
      "type": "string",
      "required": false,
      "description": "Database connection string (alternative to individual parameters)",
      "sensitive": true
    },
    {
      "name": "ssl_mode",
      "type": "string",
      "required": false,
      "description": "SSL mode for connection",
      "enum": ["disable", "allow", "prefer", "require", "verify-ca", "verify-full"]
    }
  ]
}
```

## Integration with Frontend Applications

### React Example

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = 'https://api.embediq.com/api/v1';

function DataSourcesManager() {
  const [dataSources, setDataSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Get the auth token from your auth provider
  const token = localStorage.getItem('auth_token');
  
  // Configure axios with auth header
  const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  
  // Fetch data sources
  useEffect(() => {
    const fetchDataSources = async () => {
      try {
        setLoading(true);
        const response = await api.get('/datasources');
        setDataSources(response.data.datasources);
        setError(null);
      } catch (err) {
        setError('Failed to fetch data sources');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchDataSources();
  }, []);
  
  // Create a new data source
  const createDataSource = async (dataSourceData) => {
    try {
      const response = await api.post('/datasources', dataSourceData);
      setDataSources([...dataSources, response.data]);
      return response.data;
    } catch (err) {
      console.error('Failed to create data source:', err);
      throw err;
    }
  };
  
  // Validate a data source
  const validateDataSource = async (dataSourceId) => {
    try {
      const response = await api.post(`/datasources/${dataSourceId}/validate`);
      return response.data;
    } catch (err) {
      console.error('Validation failed:', err);
      throw err;
    }
  };
  
  // Delete a data source
  const deleteDataSource = async (dataSourceId) => {
    try {
      await api.delete(`/datasources/${dataSourceId}`);
      setDataSources(dataSources.filter(ds => ds.id !== dataSourceId));
    } catch (err) {
      console.error('Failed to delete data source:', err);
      throw err;
    }
  };
  
  // Render component...
}
```

### Vue.js Example

```javascript
// DataSourceService.js
import axios from 'axios';

const API_BASE_URL = 'https://api.embediq.com/api/v1';

export default {
  // Create axios instance with auth header
  getApi() {
    const token = localStorage.getItem('auth_token');
    return axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
  },
  
  // Get all data sources
  async getDataSources() {
    const api = this.getApi();
    const response = await api.get('/datasources');
    return response.data.datasources;
  },
  
  // Get a specific data source
  async getDataSource(id) {
    const api = this.getApi();
    const response = await api.get(`/datasources/${id}`);
    return response.data;
  },
  
  // Create a new data source
  async createDataSource(dataSourceData) {
    const api = this.getApi();
    const response = await api.post('/datasources', dataSourceData);
    return response.data;
  },
  
  // Update a data source
  async updateDataSource(id, dataSourceData) {
    const api = this.getApi();
    const response = await api.put(`/datasources/${id}`, dataSourceData);
    return response.data;
  },
  
  // Delete a data source
  async deleteDataSource(id) {
    const api = this.getApi();
    await api.delete(`/datasources/${id}`);
  },
  
  // Validate a data source
  async validateDataSource(id) {
    const api = this.getApi();
    const response = await api.post(`/datasources/${id}/validate`);
    return response.data;
  },
  
  // Get data source types
  async getDataSourceTypes() {
    const api = this.getApi();
    const response = await api.get('/datasources/types');
    return response.data.types;
  },
  
  // Get specific data source type info
  async getDataSourceTypeInfo(typeName) {
    const api = this.getApi();
    const response = await api.get(`/datasources/types/${typeName}`);
    return response.data;
  }
};
```

## Integration with Backend Applications

### Python Example

```python
import requests
import json

class DataSourceClient:
    def __init__(self, base_url, auth_token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
    
    def list_datasources(self):
        """List all data sources"""
        response = requests.get(
            f'{self.base_url}/datasources',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()['datasources']
    
    def get_datasource(self, datasource_id):
        """Get a specific data source"""
        response = requests.get(
            f'{self.base_url}/datasources/{datasource_id}',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def create_datasource(self, datasource_data):
        """Create a new data source"""
        response = requests.post(
            f'{self.base_url}/datasources',
            headers=self.headers,
            json=datasource_data
        )
        response.raise_for_status()
        return response.json()
    
    def update_datasource(self, datasource_id, datasource_data):
        """Update a data source"""
        response = requests.put(
            f'{self.base_url}/datasources/{datasource_id}',
            headers=self.headers,
            json=datasource_data
        )
        response.raise_for_status()
        return response.json()
    
    def delete_datasource(self, datasource_id):
        """Delete a data source"""
        response = requests.delete(
            f'{self.base_url}/datasources/{datasource_id}',
            headers=self.headers
        )
        response.raise_for_status()
        return True
    
    def validate_datasource(self, datasource_id):
        """Validate a data source"""
        response = requests.post(
            f'{self.base_url}/datasources/{datasource_id}/validate',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_datasource_types(self):
        """Get all data source types"""
        response = requests.get(
            f'{self.base_url}/datasources/types',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()['types']
    
    def get_datasource_type_info(self, type_name):
        """Get information about a specific data source type"""
        response = requests.get(
            f'{self.base_url}/datasources/types/{type_name}',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage example
if __name__ == '__main__':
    client = DataSourceClient(
        base_url='https://api.embediq.com/api/v1',
        auth_token='your_auth_token'
    )
    
    # List all data sources
    datasources = client.list_datasources()
    print(f"Found {len(datasources)} data sources")
    
    # Create a new PostgreSQL data source
    new_datasource = client.create_datasource({
        "name": "Analytics DB",
        "type": "postgres",
        "description": "Analytics database",
        "host": "analytics-db.example.com",
        "port": 5432,
        "database": "analytics",
        "username": "analyst",
        "password": "secure_password"
    })
    print(f"Created new data source with ID: {new_datasource['id']}")
    
    # Validate the data source
    validation_result = client.validate_datasource(new_datasource['id'])
    if validation_result['success']:
        print("Data source validation successful!")
    else:
        print(f"Validation failed: {validation_result['message']}")
```

### Node.js Example

```javascript
const axios = require('axios');

class DataSourceClient {
  constructor(baseUrl, authToken) {
    this.baseUrl = baseUrl;
    this.headers = {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json'
    };
  }
  
  async listDataSources() {
    try {
      const response = await axios.get(
        `${this.baseUrl}/datasources`,
        { headers: this.headers }
      );
      return response.data.datasources;
    } catch (error) {
      console.error('Error listing data sources:', error.message);
      throw error;
    }
  }
  
  async getDataSource(dataSourceId) {
    try {
      const response = await axios.get(
        `${this.baseUrl}/datasources/${dataSourceId}`,
        { headers: this.headers }
      );
      return response.data;
    } catch (error) {
      console.error(`Error getting data source ${dataSourceId}:`, error.message);
      throw error;
    }
  }
  
  async createDataSource(dataSourceData) {
    try {
      const response = await axios.post(
        `${this.baseUrl}/datasources`,
        dataSourceData,
        { headers: this.headers }
      );
      return response.data;
    } catch (error) {
      console.error('Error creating data source:', error.message);
      throw error;
    }
  }
  
  async updateDataSource(dataSourceId, dataSourceData) {
    try {
      const response = await axios.put(
        `${this.baseUrl}/datasources/${dataSourceId}`,
        dataSourceData,
        { headers: this.headers }
      );
      return response.data;
    } catch (error) {
      console.error(`Error updating data source ${dataSourceId}:`, error.message);
      throw error;
    }
  }
  
  async deleteDataSource(dataSourceId) {
    try {
      await axios.delete(
        `${this.baseUrl}/datasources/${dataSourceId}`,
        { headers: this.headers }
      );
      return true;
    } catch (error) {
      console.error(`Error deleting data source ${dataSourceId}:`, error.message);
      throw error;
    }
  }
  
  async validateDataSource(dataSourceId) {
    try {
      const response = await axios.post(
        `${this.baseUrl}/datasources/${dataSourceId}/validate`,
        {},
        { headers: this.headers }
      );
      return response.data;
    } catch (error) {
      console.error(`Error validating data source ${dataSourceId}:`, error.message);
      throw error;
    }
  }
  
  async getDataSourceTypes() {
    try {
      const response = await axios.get(
        `${this.baseUrl}/datasources/types`,
        { headers: this.headers }
      );
      return response.data.types;
    } catch (error) {
      console.error('Error getting data source types:', error.message);
      throw error;
    }
  }
  
  async getDataSourceTypeInfo(typeName) {
    try {
      const response = await axios.get(
        `${this.baseUrl}/datasources/types/${typeName}`,
        { headers: this.headers }
      );
      return response.data;
    } catch (error) {
      console.error(`Error getting data source type info for ${typeName}:`, error.message);
      throw error;
    }
  }
}

// Usage example
async function main() {
  const client = new DataSourceClient(
    'https://api.embediq.com/api/v1',
    'your_auth_token'
  );
  
  try {
    // List all data sources
    const dataSources = await client.listDataSources();
    console.log(`Found ${dataSources.length} data sources`);
    
    // Create a new S3 data source
    const newDataSource = await client.createDataSource({
      name: "Data Lake",
      type: "s3",
      description: "Main data lake storage",
      bucket: "company-data-lake",
      region: "us-east-1",
      access_key: "AKIAXXXXXXXXXXXXXXXX",
      secret_key: "your_secret_key",
      prefix: "analytics/"
    });
    console.log(`Created new data source with ID: ${newDataSource.id}`);
    
    // Validate the data source
    const validationResult = await client.validateDataSource(newDataSource.id);
    if (validationResult.success) {
      console.log("Data source validation successful!");
    } else {
      console.log(`Validation failed: ${validationResult.message}`);
    }
  } catch (error) {
    console.error('An error occurred:', error);
  }
}

main();
```

## Extending with Custom Data Source Types

The Data Source Configuration API supports custom data source types through its extension system. To create a custom data source type:

1. Create a new Python module in the `src/app/extensions/datasources/` directory
2. Define a class that extends `DataSourceConfig` for your custom type
3. Implement an extension class with the required methods:
   - `get_type_name()`: Returns the type name
   - `get_model_class()`: Returns the model class
   - `get_description()`: Returns a description of the type
   - `get_parameters()`: Returns parameter definitions
   - `get_validator_func()`: Returns a validation function

Example:

```python
from app.models.datasources import DataSourceConfig, ValidationResult
from pydantic import Field, SecretStr

class ElasticsearchDataSource(DataSourceConfig):
    """Model for Elasticsearch data sources"""
    
    type: str = Field("elasticsearch", description="Elasticsearch data source")
    hosts: list[str] = Field(..., description="Elasticsearch hosts")
    index: str = Field(..., description="Elasticsearch index")
    username: Optional[str] = Field(None, description="Elasticsearch username")
    password: Optional[SecretStr] = Field(None, description="Elasticsearch password")
    # Add other fields as needed

class ElasticsearchExtension:
    """Elasticsearch data source extension"""
    
    def get_type_name(self) -> str:
        return "elasticsearch"
        
    def get_model_class(self) -> Type[DataSourceConfig]:
        return ElasticsearchDataSource
        
    def get_description(self) -> str:
        return "Elasticsearch database"
        
    def get_parameters(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "hosts",
                "type": "array",
                "required": True,
                "description": "Elasticsearch hosts"
            },
            {
                "name": "index",
                "type": "string",
                "required": True,
                "description": "Elasticsearch index"
            },
            # Add other parameters
        ]
        
    async def validate_elasticsearch(self, config: ElasticsearchDataSource) -> ValidationResult:
        # Implement validation logic
        # Return ValidationResult
        
    def get_validator_func(self) -> Callable:
        return self.validate_elasticsearch
```

## Security Considerations

- **Authentication**: All endpoints require a valid JWT token
- **Encryption**: Sensitive data (passwords, tokens, keys) is encrypted at rest
- **User Isolation**: Each user's data sources are stored separately
- **Input Validation**: All inputs are validated using Pydantic models
- **Secure Defaults**: Secure defaults are used for all configuration options

## Error Handling

The API uses standard HTTP status codes for error responses:

- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server-side error

Error responses include a detail message explaining the error:

```json
{
  "detail": "Data source configuration not found"
}
```

## Conclusion

The Data Source Configuration API provides a powerful and flexible way to manage external data sources in the EmbedIQ platform. With support for various data source types, secure storage, validation, and extensibility, it enables seamless integration with different data sources while maintaining security and reliability.

For any questions or issues, please contact the EmbedIQ support team.
