import pytest
from fastapi.testclient import TestClient
import json
import logging
import os
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

from app.main import app
from app.services.rag_manager import LRURAGManager, get_rag_manager
from app.config import AUTH0_DOMAIN, AUTH0_API_AUDIENCE

logger = logging.getLogger(__name__)

# Test client
client = TestClient(app)

# Mock token for testing
TEST_TOKEN = "test_token"
TEST_USER_ID = "test_user_123"


# Mock the validate_token dependency
@pytest.fixture
def mock_validate_token():
    """Mock the validate_token dependency to return a test user ID"""
    with patch("app.middleware.auth.validate_and_decode_token") as mock_validate:
        mock_validate.return_value = {"sub": TEST_USER_ID}
        yield


# Create a mock response object for the query endpoint
class MockQueryResponse:
    def __init__(self):
        self.response = "This is a test answer from LightRAG."
        self.confidence = 0.92
        self.chunks = [
            {
                "text": "This is a test chunk for EmbedIQ query.",
                "similarity": 0.88,
                "document_id": "doc123",
                "document_title": "Test Document",
                "chunk_id": "chunk123",
                "metadata": {"page": 1},
            }
        ]


# Mock the get_rag_for_user dependency
@pytest.fixture
def mock_rag_instance():
    """Mock the LightRAG instance returned by get_rag_for_user"""
    # Create a mock LightRAG instance
    mock_rag = MagicMock()

    # Create test search results
    search_results = [
        {
            "text": "This is a test chunk for EmbedIQ.",
            "similarity": 0.85,
            "document_id": "doc123",
            "document_title": "Test Document",
            "chunk_id": "chunk123",
            "metadata": {"page": 1},
        }
    ]

    # Mock the search method with synchronous return value
    mock_rag.search.return_value = search_results

    # Create a mock response object for queries
    mock_response = MockQueryResponse()

    # Set up proper AsyncMock for async methods
    mock_rag.asearch = AsyncMock(return_value=search_results)
    mock_rag.aquery = AsyncMock(return_value=mock_response)

    # Setup the mock RAG manager
    with patch("app.dependencies.get_rag_manager") as mock_get_manager:
        manager = MagicMock()
        manager.get_instance.return_value = mock_rag
        mock_get_manager.return_value = manager

        # Patch both search_lightrag and query_lightrag utilities with AsyncMock
        with patch(
            "app.utilities.lightrag_utils.query_lightrag", new_callable=AsyncMock
        ) as mock_query, patch(
            "app.utilities.lightrag_utils.search_lightrag", new_callable=AsyncMock
        ) as mock_search:
            mock_query.return_value = mock_response
            mock_search.return_value = search_results
            yield mock_rag


def test_search_endpoint(mock_validate_token, mock_rag_instance):
    """Test the search endpoint"""
    # Prepare request data
    search_data = {
        "query": "test query",
        "max_chunks": 5,
        "threshold": 0.7,
        "mode": "hybrid",
    }

    # Send POST request to search endpoint
    response = client.post(
        "/api/v1/search",
        json=search_data,
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "results" in data
    assert "total" in data
    assert "query" in data
    assert "elapsed_time" in data

    # Check results content
    assert len(data["results"]) > 0
    assert data["total"] == len(data["results"])
    assert data["query"] == search_data["query"]

    # Since we're using AsyncMock, verify either search or asearch was called
    if hasattr(mock_rag_instance, "asearch"):
        assert mock_rag_instance.asearch.called or mock_rag_instance.search.called


def test_query_endpoint(mock_validate_token, mock_rag_instance):
    """Test the query endpoint"""
    # Prepare request data
    query_data = {"query": "What is EmbedIQ?", "max_chunks": 5, "mode": "hybrid"}

    # Send POST request to query endpoint
    response = client.post(
        "/api/v1/query",
        json=query_data,
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )

    # Verify response
    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "answer" in data
    assert "sources" in data
    assert "query" in data
    assert "elapsed_time" in data
    assert "confidence" in data

    # Check content
    assert data["answer"] == "This is a test answer from LightRAG."
    assert len(data["sources"]) > 0
    assert data["query"] == query_data["query"]
    assert data["confidence"] == 0.92


def test_search_endpoint_validation(mock_validate_token, mock_rag_instance):
    """Test the validation of search endpoint parameters"""
    # Test with invalid mode
    search_data = {
        "query": "test query",
        "max_chunks": 5,
        "threshold": 0.7,
        "mode": "invalid_mode",  # Invalid mode
    }

    response = client.post(
        "/api/v1/search",
        json=search_data,
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )

    # Mode should be corrected to "hybrid" without error
    assert response.status_code == 200

    # Test with out-of-range max_chunks
    search_data = {
        "query": "test query",
        "max_chunks": 50,  # Too high
        "threshold": 0.7,
        "mode": "hybrid",
    }

    response = client.post(
        "/api/v1/search",
        json=search_data,
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )

    # Should fail validation
    assert response.status_code == 422


def test_query_endpoint_auth(mock_rag_instance):
    """Test that query endpoint requires authentication"""
    # Send request without auth header
    query_data = {"query": "What is EmbedIQ?", "max_chunks": 5, "mode": "hybrid"}

    response = client.post("/api/v1/query", json=query_data)

    # Should return 401 Unauthorized
    assert response.status_code == 401
