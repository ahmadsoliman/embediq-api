from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.middleware.auth import validate_token
from typing import Dict, Any, Optional
import logging

# Import routers
from app.routes.documents import documents_router
from app.routes.search import search_router
from app.routes.graph import graph_router
from app.routes.datasources import datasources_router
from app.routes.monitoring import monitoring_router
from app.routes.backup import backup_router
from app.routes.config import config_router
from app.routes.docs import docs_router

logger = logging.getLogger(__name__)

# Add debug logging
logger.info("API router module loading")
logger.info(f"Documents router has {len(documents_router.routes)} routes")
for route in documents_router.routes:
    logger.info(f"Route: {route.path}, methods: {route.methods}")

logger.info(f"Search router has {len(search_router.routes)} routes")
for route in search_router.routes:
    logger.info(f"Route: {route.path}, methods: {route.methods}")

logger.info(f"Graph router has {len(graph_router.routes)} routes")
for route in graph_router.routes:
    logger.info(f"Route: {route.path}, methods: {route.methods}")

# Create API router
api_router = APIRouter(prefix="/api/v1")

# Include other routers
logger.info("Including documents_router in api_router")
api_router.include_router(documents_router, prefix="/documents")
logger.info("Including search_router in api_router")
api_router.include_router(search_router)
logger.info("Including graph_router in api_router")
api_router.include_router(graph_router, prefix="/graph")
logger.info("Including datasources_router in api_router")
api_router.include_router(datasources_router, prefix="/datasources")
logger.info("Including monitoring_router in api_router")
api_router.include_router(monitoring_router)
logger.info("Including backup_router in api_router")
api_router.include_router(backup_router)
logger.info("Including config_router in api_router")
api_router.include_router(config_router)
logger.info("Including docs_router in api_router")
api_router.include_router(docs_router)
logger.info(f"API router now has {len(api_router.routes)} routes")


# Auth endpoints
@api_router.get("/auth/token", tags=["auth"])
async def validate_auth_token(request: Request, user_id: str = Depends(validate_token)):
    """
    Validate the JWT token and return token information

    This endpoint validates the JWT token in the Authorization header
    and returns basic token information including the user ID and
    permissions if available.
    """
    # Get the claims from the request state
    claims = getattr(request.state, "user_claims", {})

    # Extract token metadata
    permissions = claims.get("permissions", [])
    scopes = claims.get("scope", "").split()

    response = {
        "valid": True,
        "user_id": user_id,
        "permissions": permissions,
        "scopes": scopes,
        "token_metadata": {
            "iss": claims.get("iss"),
            "aud": claims.get("aud"),
            "exp": claims.get("exp"),
            "iat": claims.get("iat"),
        },
    }

    logger.info(f"Token validated for user {user_id}")
    return response


@api_router.get("/auth/profile", tags=["auth"])
async def get_user_profile(request: Request, user_id: str = Depends(validate_token)):
    """
    Get the user profile information

    Returns user profile information based on the validated JWT token.
    In a production environment, this would fetch additional user details
    from Auth0's Management API or a user database.
    """
    # Get the claims from the request state
    claims = getattr(request.state, "user_claims", {})

    # Extract profile information
    # In production, consider fetching more details from Auth0's Management API
    profile = {
        "user_id": user_id,
        "email": claims.get("email", ""),
        "name": claims.get("name", ""),
        "nickname": claims.get("nickname", ""),
        "picture": claims.get("picture", ""),
        "email_verified": claims.get("email_verified", False),
        "updated_at": claims.get("updated_at", ""),
    }

    logger.info(f"Profile retrieved for user {user_id}")
    return {"profile": profile}
