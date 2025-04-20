import logging
import json
from typing import Dict, List, Optional, Any
import httpx
from jose import jwt, jwk, JWTError
from fastapi import HTTPException, status
from app.config import AUTH0_DOMAIN, AUTH0_API_AUDIENCE

logger = logging.getLogger(__name__)

# Cache for Auth0 public keys
_jwks_cache: Optional[Dict[str, Any]] = None
_jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"


async def get_auth0_public_keys() -> Dict[str, Any]:
    """
    Fetch and cache Auth0 public keys from the JWKS endpoint

    Returns:
        Dictionary containing Auth0 public keys
    """
    global _jwks_cache

    if _jwks_cache is not None:
        return _jwks_cache

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(_jwks_url)
            response.raise_for_status()
            _jwks_cache = response.json()
            return _jwks_cache
    except (httpx.HTTPError, json.JSONDecodeError) as e:
        logger.error(f"Error fetching Auth0 public keys: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to fetch authentication keys",
        )


def get_key_from_jwks(token: str, jwks: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Get the correct key from JWKS based on the token's kid

    Args:
        token: JWT token
        jwks: JSON Web Key Set

    Returns:
        The matching key or None if not found
    """
    try:
        # Get the key ID from the token header
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        if not kid:
            logger.error("No key ID found in token")
            return None

        # Find the key with the matching ID
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return key

        logger.error(f"No matching key found for kid {kid}")
        return None
    except Exception as e:
        logger.error(f"Error extracting key ID from token: {str(e)}")
        return None


async def validate_and_decode_token(token: str) -> Dict[str, Any]:
    """
    Validate and decode a JWT token using Auth0 public keys

    Args:
        token: JWT token to validate

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token validation fails
    """
    try:
        # Get Auth0 public keys
        jwks = await get_auth0_public_keys()

        # Get the key matching the token's kid
        key = get_key_from_jwks(token, jwks)
        if not key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token signature",
            )

        # Convert JWK to PEM format for verification
        public_key = jwk.construct(key)

        # Verify and decode the token
        payload = jwt.decode(
            token,
            public_key.to_pem().decode("utf-8"),
            algorithms=[key.get("alg", "RS256")],
            audience=AUTH0_API_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/",
        )

        return payload
    except JWTError as e:
        logger.error(f"JWT validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error validating token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication error",
        )


def extract_user_id(payload: Dict[str, Any]) -> str:
    """
    Extract the user ID from a token payload

    Args:
        payload: Decoded token payload

    Returns:
        User ID extracted from the token

    Raises:
        HTTPException: If user ID cannot be extracted
    """
    # Auth0 uses 'sub' claim for the user ID
    user_id = payload.get("sub")

    if not user_id:
        logger.error("No user ID found in token payload")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user information in token",
        )

    return user_id
