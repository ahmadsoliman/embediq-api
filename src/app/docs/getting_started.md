# Getting Started

This document provides instructions for setting up and running the EmbedIQ backend for development.

## Prerequisites

- Python 3.10 or later
- PostgreSQL 14 or later
- Docker and Docker Compose (optional, for containerized development)
- Git

## Clone the Repository

```bash
git clone https://github.com/yourusername/embediq-backend.git
cd embediq-backend
```

## Local Development Setup

### 1. Create a Virtual Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up the Database

Follow the instructions in the [Database Setup](database_setup.md) documentation to set up a PostgreSQL database.

### 4. Configure Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/embediq

# Auth0
AUTH0_DOMAIN=your-auth0-domain.auth0.com
AUTH0_API_AUDIENCE=your-auth0-api-audience

# For development, you can disable authentication
AUTH_DISABLED=true

# Data directory
DATA_DIR=./data/embediq/users
```

See the [Environment Variables](environment_variables.md) documentation for more details.

### 5. Run the Development Server

```bash
# From the src directory
cd src
python run_dev_server.py --reload
```

The API will be available at http://localhost:8000.

## Docker Development Setup

### 1. Configure Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Database
DATABASE_URL=postgresql://postgres:devpassword@db:5432/embediq

# Auth0
AUTH0_DOMAIN=your-auth0-domain.auth0.com
AUTH0_API_AUDIENCE=your-auth0-api-audience

# For development, you can disable authentication
AUTH_DISABLED=true

# Data directory
DATA_DIR=/data/embediq/users
```

### 2. Start Docker Containers

```bash
docker-compose up -d
```

The API will be available at http://localhost:8000.

### 3. View Logs

```bash
docker-compose logs -f api
```

## Testing the API

### 1. Check the API Health

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "database": {
    "connected": true,
    "extensions": {
      "uuid-ossp": true,
      "pg_trgm": true,
      "vector": true
    }
  },
  "data_directory": {
    "path": "/data/embediq/users",
    "exists": true,
    "writable": true
  }
}
```

### 2. Access the API Documentation

Open http://localhost:8000/docs in your browser to access the Swagger UI documentation.

### 3. Test Authentication

If authentication is enabled, you'll need to obtain a JWT token from Auth0. For development, you can use the Auth0 Dashboard to create a test token.

```bash
# Test the token validation endpoint
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" http://localhost:8000/api/v1/auth/token
```

Expected response:

```json
{
  "valid": true,
  "user_id": "auth0|123456789",
  "permissions": [],
  "scopes": ["openid", "profile", "email"],
  "token_metadata": {
    "iss": "https://your-auth0-domain.auth0.com/",
    "aud": "your-auth0-api-audience",
    "exp": 1619712000,
    "iat": 1619625600
  }
}
```

## Project Structure

```
embediq-backend/
├── .env                  # Environment variables
├── docker-compose.yml    # Docker Compose configuration
├── requirements.txt      # Python dependencies
├── src/                  # Source code
│   ├── app/              # Application code
│   │   ├── config/       # Configuration
│   │   ├── db/           # Database utilities
│   │   ├── docs/         # Documentation
│   │   ├── middleware/   # Middleware
│   │   ├── models/       # Data models
│   │   ├── routes/       # API routes
│   │   ├── services/     # Business logic
│   │   ├── utilities/    # Utility functions
│   │   ├── main.py       # FastAPI application
│   │   └── __init__.py   # Package initialization
│   ├── tests/            # Tests
│   │   ├── integration/  # Integration tests
│   │   ├── unit/         # Unit tests
│   │   └── __init__.py   # Package initialization
│   └── run_dev_server.py # Development server script
└── README.md             # Project README
```

## Development Workflow

1. **Create a Feature Branch**: Create a new branch for your feature or bug fix.

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**: Implement your changes and write tests.

3. **Run Tests**: Run the tests to ensure your changes don't break existing functionality.

   ```bash
   # Run all tests
   pytest
   
   # Run specific tests
   pytest src/tests/unit/test_file.py
   ```

4. **Format Code**: Format your code using Black.

   ```bash
   black src/
   ```

5. **Lint Code**: Lint your code using Flake8.

   ```bash
   flake8 src/
   ```

6. **Commit Changes**: Commit your changes with a descriptive message.

   ```bash
   git add .
   git commit -m "Add your feature description"
   ```

7. **Push Changes**: Push your changes to the remote repository.

   ```bash
   git push origin feature/your-feature-name
   ```

8. **Create a Pull Request**: Create a pull request on GitHub.

## Next Steps

- [API Overview](api_overview.md): Learn about the API endpoints.
- [Authentication](authentication.md): Learn about authentication and authorization.
- [Testing](testing.md): Learn about testing the application.
- [Deployment](deployment.md): Learn about deploying the application.
