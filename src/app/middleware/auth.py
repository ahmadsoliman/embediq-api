from fastapi import Request, HTTPException, status
import logging
from app.utilities.auth import validate_and_decode_token, extract_user_id

logger = logging.getLogger(__name__)


async def validate_token(request: Request):
    """
    Validate JWT token from Authorization header

    Extracts the token from the Authorization header,
    validates it using Auth0 public keys, and returns the user ID.

    Args:
        request: The FastAPI request

    Returns:
        The validated user ID

    Raises:
        HTTPException: If authentication fails
    """
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        logger.warning("Missing authentication token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )

    # Validate and decode the token using the helper function
    payload = await validate_and_decode_token(token)

    # Extract user ID
    user_id = extract_user_id(payload)

    # Store additional user info in request state
    request.state.user_id = user_id
    request.state.user_claims = payload

    return user_id


class AuthError(Exception):
    """Authentication error with status code and detail message"""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"{status_code}: {detail}")


def get_token_from_header(request: Request) -> str:
    """
    Extract the JWT token from the Authorization header

    Args:
        request: The FastAPI request

    Returns:
        The JWT token

    Raises:
        AuthError: If the token is missing or malformed
    """
    auth_header = request.headers.get("Authorization", "")

    if not auth_header:
        raise AuthError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing",
        )

    parts = auth_header.split()

    if parts[0].lower() != "bearer":
        raise AuthError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must start with Bearer",
        )

    if len(parts) != 2:
        raise AuthError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must be Bearer token",
        )

    return parts[1]
