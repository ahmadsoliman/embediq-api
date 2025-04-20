# EmbedIQ Backend

This is the backend for the EmbedIQ application, providing a REST API for document management, vector search, and query capabilities using LightRAG.

## Running the Server

### Development Mode

To run the server in development mode with auto-reload:

```bash
cd src
python run_dev_server.py --reload
```

Options:

- `--host`: Host to bind the server to (default: 0.0.0.0)
- `--port`: Port to bind the server to (default: 8000)
- `--reload`: Enable auto-reload on code changes

### With Docker Compose

From the project root:

```bash
docker-compose up
```

## Testing Auth0 Integration

The backend includes testing tools to verify the Auth0 integration.

### Getting a Test Token

To test authenticated endpoints, you'll need a valid Auth0 token. You can either:

1. Use the Auth0 Dashboard:

   - Go to the Auth0 Dashboard (https://manage.auth0.com/)
   - Select your application
   - Go to the API section and select your API
   - Navigate to the 'Test' tab
   - Use the 'OAuth2 Debug Console' to generate a test token

2. Use the Auth0 API Explorer:
   - Go to: https://auth0.com/docs/api/authentication
   - Find the 'Get Token' section
   - Fill in your Auth0 domain, client ID, and client secret
   - Generate a token

### Running the Auth Test Script

To test the Auth0 integration with a running server:

```bash
cd src
python -m tests.test_auth_integration --token "your-auth0-token"
```

Options:

- `--url`: Base URL for the backend (default: http://localhost:8000)
- `--token`: Auth0 JWT token for testing
- `--token-help`: Display instructions for getting an Auth0 test token

## API Endpoints

### Authentication

- `GET /api/v1/auth/token`: Validate JWT token and return user information
- `GET /api/v1/auth/profile`: Get user profile information

### Data Management

- `GET /api/v1/documents`: List documents (coming soon)
- `POST /api/v1/documents`: Upload a document (coming soon)

### Search and Query

- `GET /api/v1/search`: Vector similarity search (coming soon)
- `GET /api/v1/query`: Combined RAG-powered queries (coming soon)

## Environment Variables

See `.env.example` for the list of required environment variables.

## Running Tests

To run unit tests:

```bash
cd src
pytest
```
