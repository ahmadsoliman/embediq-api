import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
import jwt
import time
from unittest.mock import patch, AsyncMock
from app.main import app
from app.utilities.auth import validate_and_decode_token, extract_user_id
from app.middleware.auth import validate_token, get_token_from_header, AuthError


# Create a test client
client = TestClient(app)


def create_mock_token(sub="123456", expired=False, invalid_signature=False):
    """Create a mock JWT token for testing"""
    # Mock payload
    payload = {
        "sub": sub,
        "name": "Test User",
        "email": "test@example.com",
        "iss": f"https://dev-example.auth0.com/",
        "aud": "https://api.example.com",
        "exp": int(time.time()) - 3600 if expired else int(time.time()) + 3600,
        "iat": int(time.time()),
        "permissions": ["read:documents", "write:documents"],
    }

    # Secret key for testing (would be public/private key pair in production)
    secret = "test_secret"

    if invalid_signature:
        secret = "wrong_secret"

    # Create token
    token = jwt.encode(payload, secret, algorithm="HS256")

    return token


@pytest.mark.asyncio
@patch("app.utilities.auth.get_auth0_public_keys")
@patch("app.utilities.auth.get_key_from_jwks")
@patch("jose.jwt.decode")
async def test_validate_and_decode_token(mock_decode, mock_get_key, mock_get_keys):
    """Test the validate_and_decode_token function"""
    # Mock return values
    mock_get_keys.return_value = {"keys": [{"kid": "test_kid", "kty": "RSA"}]}
    mock_get_key.return_value = {"kid": "test_kid", "kty": "RSA"}

    # Mock the JWT decode function
    mock_decode.return_value = {"sub": "123456", "name": "Test User"}

    # Test with a valid token
    token = "valid_token"
    result = await validate_and_decode_token(token)

    # Assert the JWT decode function was called
    mock_decode.assert_called_once()

    # Check the result
    assert result["sub"] == "123456"
    assert result["name"] == "Test User"


@pytest.mark.asyncio
@patch("app.utilities.auth.get_auth0_public_keys")
async def test_validate_and_decode_token_no_matching_key(mock_get_keys):
    """Test when no matching key is found"""
    # Mock return values
    mock_get_keys.return_value = {"keys": []}

    # Test with a token that has no matching key
    token = "token_with_no_matching_key"

    # Should raise an HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await validate_and_decode_token(token)

    # Check the exception
    assert exc_info.value.status_code == 401
    assert "Invalid token signature" in exc_info.value.detail


def test_extract_user_id():
    """Test the extract_user_id function"""
    # Test with a valid payload
    payload = {"sub": "123456"}
    user_id = extract_user_id(payload)
    assert user_id == "123456"

    # Test with a missing sub claim
    payload = {"name": "Test User"}
    with pytest.raises(HTTPException) as exc_info:
        extract_user_id(payload)

    # Check the exception
    assert exc_info.value.status_code == 401
    assert "Invalid user information" in exc_info.value.detail


@pytest.mark.asyncio
@patch("app.middleware.auth.validate_and_decode_token")
async def test_validate_token(mock_validate):
    """Test the validate_token middleware function"""
    # Mock the validate_and_decode_token function
    mock_validate.return_value = {"sub": "123456", "name": "Test User"}

    # Create a mock request
    mock_request = AsyncMock()
    mock_request.headers = {"Authorization": "Bearer valid_token"}
    mock_request.state = AsyncMock()

    # Call the function
    user_id = await validate_token(mock_request)

    # Check the result
    assert user_id == "123456"
    assert mock_request.state.user_id == "123456"
    assert mock_request.state.user_claims == {"sub": "123456", "name": "Test User"}


@pytest.mark.asyncio
async def test_validate_token_missing_token():
    """Test the validate_token middleware function with a missing token"""
    # Create a mock request with no Authorization header
    mock_request = AsyncMock()
    mock_request.headers = {}

    # Should raise an HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await validate_token(mock_request)

    # Check the exception
    assert exc_info.value.status_code == 401
    assert "Missing authentication token" in exc_info.value.detail


def test_get_token_from_header():
    """Test the get_token_from_header function"""
    # Create a mock request with a valid header
    mock_request = AsyncMock()
    mock_request.headers = {"Authorization": "Bearer valid_token"}

    # Call the function
    token = get_token_from_header(mock_request)

    # Check the result
    assert token == "valid_token"

    # Test with missing header
    mock_request.headers = {}
    with pytest.raises(AuthError) as exc_info:
        get_token_from_header(mock_request)
    assert exc_info.value.status_code == 401
    assert "missing" in exc_info.value.detail

    # Test with invalid header format
    mock_request.headers = {"Authorization": "Basic valid_token"}
    with pytest.raises(AuthError) as exc_info:
        get_token_from_header(mock_request)
    assert exc_info.value.status_code == 401
    assert "Bearer" in exc_info.value.detail

    # Test with invalid header parts
    mock_request.headers = {"Authorization": "Bearer token extra"}
    with pytest.raises(AuthError) as exc_info:
        get_token_from_header(mock_request)
    assert exc_info.value.status_code == 401
