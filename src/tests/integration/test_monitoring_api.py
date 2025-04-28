"""
Integration tests for monitoring API.
"""

import pytest
from fastapi.testclient import TestClient
import json
import logging
import os
from unittest.mock import patch, MagicMock

from app.main import app
from app.middleware.auth import admin_required

logger = logging.getLogger(__name__)

# Test client
client = TestClient(app)

# Mock admin user ID for testing
TEST_ADMIN_ID = "admin_user_123"


# Mock the admin_required dependency
@pytest.fixture
def mock_admin_required():
    """Mock the admin_required dependency to return a test admin user ID"""
    # Patch the ADMIN_USER_IDS in the config
    with patch("app.middleware.auth.ADMIN_USER_IDS", [TEST_ADMIN_ID]):
        # Mock the validate_token dependency
        with patch("app.middleware.auth.validate_token") as mock_validate:
            mock_validate.return_value = TEST_ADMIN_ID

            # Then mock the admin_required dependency
            with patch("app.middleware.auth.admin_required") as mock_admin:
                mock_admin.return_value = TEST_ADMIN_ID

                # Also patch the request validation in the test client
                with patch(
                    "app.middleware.auth.validate_and_decode_token"
                ) as mock_validate_decode:
                    mock_validate_decode.return_value = {"sub": TEST_ADMIN_ID}
                    yield


class TestMonitoringAPI:
    """Tests for monitoring API endpoints"""

    def test_get_system_metrics(self, mock_admin_required):
        """Test GET /api/v1/monitoring/system endpoint"""
        response = client.get(
            "/api/v1/monitoring/system", headers={"Authorization": "Bearer test_token"}
        )

        # Check response
        assert response.status_code == 200
        data = response.json()

        # Check that response contains expected keys
        assert "timestamp" in data
        assert "uptime_seconds" in data
        assert "cpu" in data
        assert "memory" in data
        assert "disk" in data
        assert "network" in data
        assert "process" in data

    def test_get_lightrag_metrics(self, mock_admin_required):
        """Test GET /api/v1/monitoring/lightrag endpoint"""
        response = client.get(
            "/api/v1/monitoring/lightrag",
            headers={"Authorization": "Bearer test_token"},
        )

        # Check response
        assert response.status_code == 200
        data = response.json()

        # Check that response contains expected keys
        assert "timestamp" in data
        assert "uptime_seconds" in data
        assert "operations" in data
        assert "throughput" in data
        assert "query" in data
        assert "search" in data
        assert "insert" in data

    def test_reset_lightrag_metrics(self, mock_admin_required):
        """Test POST /api/v1/monitoring/lightrag/reset endpoint"""
        response = client.post(
            "/api/v1/monitoring/lightrag/reset",
            headers={"Authorization": "Bearer test_token"},
        )

        # Check response
        assert response.status_code == 200
        data = response.json()

        # Check that response contains success message
        assert "message" in data
        assert "reset successfully" in data["message"]

    def test_get_health_check(self):
        """Test GET /api/v1/monitoring/health endpoint"""
        response = client.get("/api/v1/monitoring/health")

        # Check response
        assert response.status_code == 200
        data = response.json()

        # Check that response contains expected keys
        assert "status" in data
        assert "timestamp" in data
        assert "checks" in data
        assert "metrics" in data

        # Check status
        assert data["status"] in ["healthy", "unhealthy"]

        # Check checks
        assert "cpu" in data["checks"]
        assert "memory" in data["checks"]
        assert "disk" in data["checks"]

    def test_get_user_metrics(self, mock_admin_required):
        """Test GET /api/v1/monitoring/user/{user_id} endpoint"""
        # Create a test user directory
        os.makedirs(os.path.join(os.getcwd(), "data", "test_user"), exist_ok=True)

        try:
            response = client.get(
                "/api/v1/monitoring/user/test_user",
                headers={"Authorization": "Bearer test_token"},
            )

            # Check response
            assert response.status_code == 200
            data = response.json()

            # Check that response contains expected keys
            # The response might be a "no metrics found" message if the directory is empty
            if "message" in data and "No metrics found" in data["message"]:
                assert "test_user" in data["message"]
            else:
                assert "user_id" in data
                assert data["user_id"] == "test_user"
        finally:
            # Clean up
            try:
                import shutil

                shutil.rmtree(
                    os.path.join(os.getcwd(), "data", "test_user"), ignore_errors=True
                )
            except:
                pass

    def test_unauthorized_access(self):
        """Test unauthorized access to admin-only endpoints"""
        # Patch ADMIN_USER_IDS to not include our test user
        with patch("app.middleware.auth.ADMIN_USER_IDS", ["some_other_admin"]):
            # First mock validate_token to succeed
            with patch("app.middleware.auth.validate_token") as mock_validate:
                mock_validate.return_value = "regular_user"

                # Then mock admin_required to raise HTTPException
                with patch("app.middleware.auth.admin_required") as mock_admin:
                    from fastapi import HTTPException

                    mock_admin.side_effect = HTTPException(
                        status_code=403, detail="Admin privileges required"
                    )

                    # Also patch validate_and_decode_token to return a valid token
                    with patch(
                        "app.middleware.auth.validate_and_decode_token"
                    ) as mock_validate_decode:
                        mock_validate_decode.return_value = {"sub": "regular_user"}

                        # Try to access admin-only endpoint
                        response = client.get(
                            "/api/v1/monitoring/system",
                            headers={"Authorization": "Bearer test_token"},
                        )

                        # Check response
                        assert response.status_code == 403
                        data = response.json()
                        assert "detail" in data
                        assert data["detail"] == "Admin privileges required"
