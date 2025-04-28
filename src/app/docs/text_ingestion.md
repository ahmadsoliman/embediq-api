# Text Ingestion API

The Text Ingestion API allows you to ingest plain text content directly into LightRAG without requiring a file upload. This is useful for processing text from various sources, such as user input, API responses, or extracted content.

## Endpoint

`POST /api/v1/documents/text`

## Authentication

This endpoint requires authentication using a JWT token. Include the token in the `Authorization` header:

```
Authorization: Bearer your_jwt_token
```

## Request Body

The request body should be a JSON object with the following fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | Yes | The plain text content to ingest |
| `title` | string | Yes | Title for the text content |
| `description` | string | No | Optional description for the text content |
| `tags` | array of strings | No | Optional list of tags for the text content |

Example request body:

```json
{
  "text": "This is sample text that will be ingested into LightRAG. It can contain multiple paragraphs and will be automatically chunked and processed for retrieval.",
  "title": "Sample Text Document",
  "description": "A sample text document for testing the text ingestion API",
  "tags": ["sample", "test", "text"]
}
```

## Response

The response is a JSON object containing metadata about the ingested text:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Unique identifier for the text document |
| `title` | string | Title of the text content |
| `description` | string | Description of the text content (if provided) |
| `content_length` | integer | Length of the text content in characters |
| `created_at` | string (ISO 8601) | Creation timestamp |
| `updated_at` | string (ISO 8601) | Last update timestamp |
| `tags` | array of strings | List of tags for the text content |
| `status` | string | Processing status of the text content |
| `user_id` | string | ID of the user who owns the text content |

Example response:

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Sample Text Document",
  "description": "A sample text document for testing the text ingestion API",
  "content_length": 150,
  "created_at": "2023-04-27T12:34:56.789Z",
  "updated_at": "2023-04-27T12:34:56.789Z",
  "tags": ["sample", "test", "text"],
  "status": "processing",
  "user_id": "user123"
}
```

## Status Codes

| Status Code | Description |
|-------------|-------------|
| 201 | Created - Text successfully ingested |
| 400 | Bad Request - Invalid request body or empty text |
| 401 | Unauthorized - Missing or invalid authentication token |
| 413 | Payload Too Large - Text content exceeds maximum length |
| 500 | Internal Server Error - Server error during processing |

## Examples

### cURL

```bash
curl -X POST "https://api.embediq.com/api/v1/documents/text" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is sample text that will be ingested into LightRAG.",
    "title": "Sample Text Document",
    "description": "A sample text document for testing",
    "tags": ["sample", "test"]
  }'
```

### Python

```python
import requests
import json

url = "https://api.embediq.com/api/v1/documents/text"
headers = {
    "Authorization": "Bearer your_jwt_token",
    "Content-Type": "application/json"
}
data = {
    "text": "This is sample text that will be ingested into LightRAG.",
    "title": "Sample Text Document",
    "description": "A sample text document for testing",
    "tags": ["sample", "test"]
}

response = requests.post(url, headers=headers, data=json.dumps(data))
print(response.json())
```

## Notes

- The maximum text length is 1MB (1,048,576 characters).
- Text is processed asynchronously. The initial response will have `status` set to `"processing"`.
- You can check the processing status by retrieving the document with the returned ID.
- Once processing is complete, the status will change to `"complete"` or `"failed"`.
- Ingested text is automatically chunked and embedded for retrieval using the same process as uploaded documents.
- The text content is not stored directly in the database, only the embeddings and metadata are stored.
