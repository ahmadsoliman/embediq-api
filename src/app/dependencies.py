from fastapi import Request, Depends
from lightrag import LightRAG
import logging

from app.middleware.auth import validate_token
from app.services.rag_manager import get_rag_manager

logger = logging.getLogger(__name__)


async def get_rag_for_user(
    request: Request, user_id: str = Depends(validate_token)
) -> LightRAG:
    """
    Dependency for retrieving a user-specific LightRAG instance

    This function is used with FastAPI's dependency injection system to
    provide a LightRAG instance for the authenticated user.

    Args:
        request: The FastAPI request object
        user_id: The authenticated user ID (from validate_token dependency)

    Returns:
        A LightRAG instance for the user
    """
    logger.info(f"Getting LightRAG instance for user {user_id}")

    # Get the RAG instance manager
    rag_manager = get_rag_manager()

    # Get the LightRAG instance for this user
    rag = rag_manager.get_instance(user_id)

    return rag
