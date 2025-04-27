# Integration Tests for EmbedIQ Backend

This directory contains integration tests that run against the real API and database in Docker, without mocks. These tests validate the complete functionality of the API endpoints and the integration with LightRAG.

## Prerequisites

1. Docker and Docker Compose installed
2. The EmbedIQ backend services running in Docker
3. A valid authorization token for API authentication

## Running the Tests

### 1. Start the Docker Services

Make sure the API and database services are running in Docker:

```bash
# From the project root directory
docker-compose up -d
```

### 2. Set Environment Variables

Set the following environment variables:

```bash
# The base URL of the API (default: http://localhost:8000)
export API_BASE_URL=http://localhost:8000

# Required: A valid JWT token for authentication
export TEST_AUTH_TOKEN=your_auth_token_here
```

To get a valid auth token, you can use the Auth0 login flow in the frontend application, or generate a test token using Auth0's management API.

### 3. Install Test Dependencies

```bash
pip install pytest pytest-asyncio aiohttp
```

### 4. Run the Tests

```bash
# From the project root directory
python -m pytest src/tests/integration -v
```

Or run a specific test:

```bash
python -m pytest src/tests/integration/test_documents_api.py::test_document_lifecycle -v
```

## Test Overview

The integration tests cover the following scenarios:

### Document API Tests (`test_documents_api.py`)

1. **Document Lifecycle**

   - Upload a new document with metadata
   - List documents and verify the uploaded document is present
   - Get document details by ID
   - Update document metadata (title, description, tags)
   - Delete the document
   - Verify document deletion

2. **Document Filters**
   - Upload multiple documents with different tags
   - Test filtering documents by tag
   - Test filtering documents by status (uploading/processing/complete)
   - Clean up all test documents

## Writing New Integration Tests

When writing new integration tests:

1. Use the existing `DocumentAPIClient` class or create similar clients for other API endpoints
2. Ensure proper cleanup of any test data created during tests
3. Use descriptive test names and assertions
4. Add appropriate logging for debugging test failures
5. Handle flaky conditions like asynchronous processing gracefully

## Troubleshooting

If tests fail, check:

1. API and database services are running properly
2. The auth token is valid and has the necessary permissions
3. Database connection string is correctly configured
4. Network connectivity between test environment and Docker services

For more detailed output, increase the log level:

```bash
export LOG_LEVEL=DEBUG
```
