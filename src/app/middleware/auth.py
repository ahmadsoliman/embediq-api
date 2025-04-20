from fastapi import Request, HTTPException, status
from jose import jwt, JWTError
from app.config import AUTH0_DOMAIN, AUTH0_API_AUDIENCE
import logging

logger = logging.getLogger(__name__)


async def validate_token(request: Request):
    """
    Validate JWT token from Authorization header
    This is a simple stub for now - will be expanded in the Auth0 integration task
    """
    try:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication token",
            )

        # Basic JWT validation - this will be expanded later
        # Currently just a placeholder for the actual implementation
        try:
            payload = jwt.decode(
                token,
                algorithms=["RS256"],
                audience=AUTH0_API_AUDIENCE,
                issuer=f"https://{AUTH0_DOMAIN}/",
            )

            # Extract user ID (will be implemented properly later)
            user_id = payload.get("sub", "")

            # Attach user info to request state
            request.state.user_id = user_id
            return user_id
        except JWTError as e:
            logger.error(f"JWT validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid authentication token: {str(e)}",
            )
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {str(e)}",
        )
