# API Overview

This document provides an overview of the EmbedIQ Backend API endpoints.

## Base URL

All API endpoints are prefixed with `/api/v1`.

## Authentication

Most API endpoints require authentication using a JWT token. The token should be included in the `Authorization` header as a Bearer token:

```
Authorization: Bearer your_jwt_token
```

See the [Authentication](authentication.md) documentation for more details.

## API Endpoints

### Documents API

| Endpoint | Method | Description | Authentication |
|----------|--------|-------------|----------------|
| `/api/v1/documents` | GET | List all documents | Required |
| `/api/v1/documents` | POST | Upload a new document | Required |
| `/api/v1/documents/{document_id}` | GET | Get document details | Required |
| `/api/v1/documents/{document_id}` | PATCH | Update document metadata | Required |
| `/api/v1/documents/{document_id}` | DELETE | Delete a document | Required |

### Search API

| Endpoint | Method | Description | Authentication |
|----------|--------|-------------|----------------|
| `/api/v1/search` | POST | Search for documents | Required |
| `/api/v1/query` | POST | Query documents with RAG | Required |

### Graph API

| Endpoint | Method | Description | Authentication |
|----------|--------|-------------|----------------|
| `/api/v1/graph/nodes` | GET | List all graph nodes | Required |
| `/api/v1/graph/nodes` | POST | Create a new node | Required |
| `/api/v1/graph/nodes/{node_id}` | GET | Get node details | Required |
| `/api/v1/graph/nodes/{node_id}` | PATCH | Update a node | Required |
| `/api/v1/graph/nodes/{node_id}` | DELETE | Delete a node | Required |
| `/api/v1/graph/edges` | GET | List all graph edges | Required |
| `/api/v1/graph/edges` | POST | Create a new edge | Required |
| `/api/v1/graph/edges/{edge_id}` | GET | Get edge details | Required |
| `/api/v1/graph/edges/{edge_id}` | PATCH | Update an edge | Required |
| `/api/v1/graph/edges/{edge_id}` | DELETE | Delete an edge | Required |
| `/api/v1/graph/search` | POST | Search the graph | Required |

### Data Sources API

| Endpoint | Method | Description | Authentication |
|----------|--------|-------------|----------------|
| `/api/v1/datasources` | GET | List all data sources | Required |
| `/api/v1/datasources` | POST | Create a new data source | Required |
| `/api/v1/datasources/{datasource_id}` | GET | Get data source details | Required |
| `/api/v1/datasources/{datasource_id}` | PATCH | Update a data source | Required |
| `/api/v1/datasources/{datasource_id}` | DELETE | Delete a data source | Required |
| `/api/v1/datasources/{datasource_id}/validate` | POST | Validate a data source | Required |

### Monitoring API

| Endpoint | Method | Description | Authentication |
|----------|--------|-------------|----------------|
| `/api/v1/monitoring/system` | GET | Get system metrics | Admin |
| `/api/v1/monitoring/lightrag` | GET | Get LightRAG performance metrics | Admin |
| `/api/v1/monitoring/lightrag/reset` | POST | Reset LightRAG performance metrics | Admin |
| `/api/v1/monitoring/health` | GET | Get health check | Public |
| `/api/v1/monitoring/user/{user_id}` | GET | Get metrics for a specific user | Admin |

### Backup API

| Endpoint | Method | Description | Authentication |
|----------|--------|-------------|----------------|
| `/api/v1/backup/status` | GET | Get backup status | Admin |
| `/api/v1/backup/history` | GET | Get backup history | Admin |
| `/api/v1/backup/trigger` | POST | Trigger a manual backup | Admin |
| `/api/v1/backup/restore/{backup_id}` | POST | Restore from a backup | Admin |

### Configuration API

| Endpoint | Method | Description | Authentication |
|----------|--------|-------------|----------------|
| `/api/v1/config/lightrag` | GET | Get LightRAG configuration | Admin |
| `/api/v1/config/lightrag` | PUT | Update LightRAG configuration | Admin |
| `/api/v1/config/lightrag/reset` | POST | Reset LightRAG configuration | Admin |

### Authentication API

| Endpoint | Method | Description | Authentication |
|----------|--------|-------------|----------------|
| `/api/v1/auth/token` | GET | Validate JWT token | Required |
| `/api/v1/auth/profile` | GET | Get user profile | Required |

## Error Handling

All API endpoints follow a consistent error handling pattern. See the [Error Handling](error_handling.md) documentation for more details.

## Rate Limiting

API endpoints may be subject to rate limiting. Rate limit information is included in the response headers:

- `X-RateLimit-Limit`: The maximum number of requests allowed in a time window
- `X-RateLimit-Remaining`: The number of requests remaining in the current time window
- `X-RateLimit-Reset`: The time when the current rate limit window resets (Unix timestamp)

## Pagination

List endpoints support pagination using the following query parameters:

- `page`: The page number (default: 1)
- `limit`: The number of items per page (default: 10, max: 100)

Pagination information is included in the response:

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "limit": 10,
  "pages": 10
}
```
