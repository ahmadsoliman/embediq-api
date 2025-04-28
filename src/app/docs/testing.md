# Testing

This document describes how to test the EmbedIQ backend.

## Test Structure

The EmbedIQ backend uses pytest for testing. Tests are organized into the following categories:

- **Unit Tests**: Test individual components in isolation.
- **Integration Tests**: Test the interaction between components.
- **End-to-End Tests**: Test the entire application from the API endpoints to the database.

## Test Directory Structure

```
src/tests/
├── __init__.py
├── conftest.py           # Shared test fixtures
├── test_auth.py          # Authentication tests
├── test_auth_integration.py  # Authentication integration tests
├── test_rag_manager.py   # RAG manager tests
├── integration/          # Integration tests
│   ├── __init__.py
│   ├── test_datasources_api.py
│   ├── test_documents_api.py
│   ├── test_graph_api.py
│   ├── test_monitoring_api.py
│   └── test_search_api.py
└── unit/                 # Unit tests
    ├── __init__.py
    ├── test_backup.py
    ├── test_datasource_models.py
    ├── test_datasource_services.py
    └── test_monitoring.py
```

## Running Tests

### Running All Tests

```bash
# From the project root
pytest

# With verbose output
pytest -v

# With coverage report
pytest --cov=app
```

### Running Specific Tests

```bash
# Run a specific test file
pytest src/tests/unit/test_backup.py

# Run a specific test function
pytest src/tests/unit/test_backup.py::test_backup_service_init

# Run tests matching a pattern
pytest -k "backup"
```

### Running Tests with Different Configurations

```bash
# Run tests with a specific database URL
DATABASE_URL=postgresql://user:password@localhost:5432/test_db pytest

# Run tests with authentication disabled
AUTH_DISABLED=true pytest
```

## Test Fixtures

The EmbedIQ backend uses pytest fixtures to set up test environments. Common fixtures are defined in `src/tests/conftest.py`.

### Database Fixtures

```python
@pytest.fixture
def test_db():
    """Create a test database and return a connection."""
    # Set up test database
    conn = psycopg2.connect(DATABASE_URL)
    yield conn
    # Clean up test database
    conn.close()
```

### Authentication Fixtures

```python
@pytest.fixture
def mock_validate_token(monkeypatch):
    """Mock the validate_token function to return a test user ID."""
    async def mock_validator(*args, **kwargs):
        return "test_user"
    monkeypatch.setattr("app.middleware.auth.validate_token", mock_validator)
```

### API Client Fixtures

```python
@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    from app.main import app
    with TestClient(app) as client:
        yield client
```

## Writing Tests

### Unit Tests

Unit tests should test individual components in isolation, mocking any dependencies.

```python
def test_backup_service_init():
    """Test the initialization of the backup service."""
    # Arrange
    backup_dir = "/tmp/test_backup"
    
    # Act
    service = BackupService(backup_dir=backup_dir)
    
    # Assert
    assert service.backup_dir == backup_dir
    assert service.scheduler is None
```

### Integration Tests

Integration tests should test the interaction between components, using real dependencies when possible.

```python
@pytest.mark.asyncio
async def test_document_lifecycle(random_text_file):
    """Test the complete document lifecycle: upload, list, get, update, delete"""
    # Check if test should be skipped
    if not AUTH_TOKEN:
        pytest.skip("TEST_AUTH_TOKEN environment variable not set")
    
    async with DocumentAPIClient(API_BASE_URL, AUTH_TOKEN) as client:
        # 1. Upload a document
        title = f"Test Document {random_string(6)}"
        description = "This is a test document for integration testing"
        tags = ["test", "integration", random_string(5)]
        
        upload_result = await client.upload_document(
            title=title, description=description, file_path=random_text_file, tags=tags
        )
        
        assert upload_result["id"] is not None
        assert upload_result["title"] == title
        assert upload_result["description"] == description
        assert set(upload_result["tags"]) == set(tags)
        
        # 2. List documents
        documents = await client.list_documents()
        assert len(documents["documents"]) > 0
        assert any(doc["id"] == upload_result["id"] for doc in documents["documents"])
        
        # 3. Get document
        document = await client.get_document(upload_result["id"])
        assert document["id"] == upload_result["id"]
        assert document["title"] == title
        
        # 4. Update document
        new_title = f"Updated Test Document {random_string(6)}"
        update_result = await client.update_document(
            upload_result["id"], title=new_title
        )
        assert update_result["title"] == new_title
        
        # 5. Delete document
        delete_result = await client.delete_document(upload_result["id"])
        assert delete_result["success"] is True
        
        # Verify document is deleted
        with pytest.raises(Exception):
            await client.get_document(upload_result["id"])
```

### API Tests

API tests should test the API endpoints using the FastAPI TestClient.

```python
def test_health_endpoint(client):
    """Test the health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

## Test Environment

The test environment should be isolated from the development and production environments. Use a separate database for testing.

### Environment Variables for Testing

```bash
# Database
DATABASE_URL=postgresql://postgres:devpassword@localhost:5432/embediq_test

# Auth0
AUTH0_DOMAIN=your-auth0-domain.auth0.com
AUTH0_API_AUDIENCE=your-auth0-api-audience

# For testing, you can disable authentication
AUTH_DISABLED=true

# Data directory
DATA_DIR=./data/embediq_test/users
```

## Continuous Integration

The EmbedIQ backend uses GitHub Actions for continuous integration. The CI pipeline runs tests on every push and pull request.

### CI Pipeline

```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: embediq_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Set up database
      run: |
        psql -h localhost -U postgres -d embediq_test -c "CREATE EXTENSION IF NOT EXISTS vector;"
        psql -h localhost -U postgres -d embediq_test -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
        psql -h localhost -U postgres -d embediq_test -c "CREATE EXTENSION IF NOT EXISTS uuid-ossp;"
      env:
        PGPASSWORD: postgres
    
    - name: Run tests
      run: |
        pytest --cov=app
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/embediq_test
        AUTH_DISABLED: true
        DATA_DIR: ./data/embediq_test/users
```

## Test Coverage

The EmbedIQ backend aims for high test coverage. Use the `--cov` option with pytest to generate a coverage report.

```bash
pytest --cov=app
```

## Mocking

The EmbedIQ backend uses the `unittest.mock` module and pytest's monkeypatch fixture for mocking.

### Mocking Functions

```python
def test_function_with_mock(monkeypatch):
    """Test a function with a mocked dependency."""
    # Arrange
    mock_dependency = MagicMock()
    mock_dependency.return_value = "mocked_value"
    monkeypatch.setattr("app.module.dependency", mock_dependency)
    
    # Act
    result = function_under_test()
    
    # Assert
    assert result == "mocked_value"
    mock_dependency.assert_called_once()
```

### Mocking Classes

```python
def test_class_with_mock(monkeypatch):
    """Test a class with a mocked dependency."""
    # Arrange
    mock_dependency = MagicMock()
    mock_dependency.method.return_value = "mocked_value"
    monkeypatch.setattr("app.module.Dependency", mock_dependency)
    
    # Act
    instance = ClassUnderTest()
    result = instance.method_that_uses_dependency()
    
    # Assert
    assert result == "mocked_value"
    mock_dependency.method.assert_called_once()
```

## Async Testing

The EmbedIQ backend uses pytest-asyncio for testing async functions.

```python
@pytest.mark.asyncio
async def test_async_function():
    """Test an async function."""
    # Arrange
    
    # Act
    result = await async_function_under_test()
    
    # Assert
    assert result == expected_value
```

## Test Data

The EmbedIQ backend uses fixtures to generate test data.

```python
@pytest.fixture
def random_text_file():
    """Create a temporary text file with random content."""
    import tempfile
    import random
    import string
    
    # Generate random content
    content = ''.join(random.choice(string.ascii_letters) for _ in range(1000))
    
    # Create temporary file
    fd, path = tempfile.mkstemp(suffix='.txt')
    with os.fdopen(fd, 'w') as f:
        f.write(content)
    
    yield path
    
    # Clean up
    os.unlink(path)
```

## Test Best Practices

1. **Arrange-Act-Assert**: Structure your tests with clear arrange, act, and assert sections.
2. **Isolation**: Tests should be isolated from each other and from the environment.
3. **Deterministic**: Tests should produce the same result every time they run.
4. **Fast**: Tests should run quickly to encourage frequent testing.
5. **Comprehensive**: Tests should cover all code paths and edge cases.
6. **Readable**: Tests should be easy to read and understand.
7. **Maintainable**: Tests should be easy to maintain and update.
