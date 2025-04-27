import os
import logging
import shutil
import asyncio
from typing import Dict, Any, Optional, Callable
from collections import OrderedDict
from app.config import DATA_DIR, VECTOR_DIMENSION, MAX_TOKEN_SIZE
from app.utilities.lightrag_utils import (
    initialize_lightrag_instance,
)

# Import LightRAG-related packages
try:
    from lightrag import LightRAG
    from lightrag.utils import EmbeddingFunc
    from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed

    LIGHTRAG_INSTALLED = True
except ImportError:
    # If LightRAG is not installed, create a mock class for development
    class LightRAG:
        def __init__(
            self,
            working_dir=None,
            llm_model_func=None,
            embedding_func=None,
            db_connection_string=None,
        ):
            self.working_dir = working_dir
            self.llm_model_func = llm_model_func
            self.embedding_func = embedding_func
            self.db_connection_string = db_connection_string

    class EmbeddingFunc:
        def __init__(self, embedding_dim=None, max_token_size=None, func=None):
            self.embedding_dim = embedding_dim
            self.max_token_size = max_token_size
            self.func = func

    # Mock the OpenAI functions
    def gpt_4o_mini_complete(*args, **kwargs):
        return "This is a mock response from gpt_4o_mini_complete"

    def openai_embed(texts):
        # Return an array of the correct dimension for each text
        return [
            [0.0] * VECTOR_DIMENSION
            for _ in range(len(texts) if isinstance(texts, list) else 1)
        ]

    LIGHTRAG_INSTALLED = False


logger = logging.getLogger(__name__)


class RAGInstanceManager:
    """
    Manager for LightRAG instances that handles creation, retrieval,
    and cleanup of user-specific LightRAG instances.
    """

    def __init__(self, base_dir: str, database_url: str, max_instances: int = 100):
        """
        Initialize the RAG instance manager

        Args:
            base_dir: The base directory for user data
            database_url: The database connection string
            max_instances: Maximum number of instances to keep in memory
        """
        self.base_dir = base_dir
        self.database_url = database_url
        self.max_instances = max_instances
        self.instances: Dict[str, LightRAG] = {}

        logger.info(f"Initialized RAGInstanceManager with base_dir={base_dir}")

    def get_instance(self, user_id: str) -> LightRAG:
        """
        Get or create a LightRAG instance for a specific user

        Args:
            user_id: The user ID

        Returns:
            A LightRAG instance
        """
        if user_id in self.instances:
            logger.info(f"Returning existing RAG instance for user {user_id}")
            return self.instances[user_id]

        # Create a new instance
        logger.info(f"Creating new RAG instance for user {user_id}")

        # For synchronous usage, run the async creation in a new event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # If no event loop exists (e.g., in a non-async context), create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.create_instance_async(user_id))

    async def create_instance_async(self, user_id: str) -> LightRAG:
        """
        Create a new LightRAG instance for a user asynchronously

        This method uses the async initialization utilities for proper setup
        of LightRAG with storages and pipeline status.

        Args:
            user_id: The user ID

        Returns:
            A new LightRAG instance
        """
        # Create user directory if it doesn't exist
        user_dir = os.path.join(self.base_dir, user_id)
        os.makedirs(user_dir, exist_ok=True)

        try:
            # Initialize LightRAG with user-specific directory using async initialization
            rag = await initialize_lightrag_instance(
                working_dir=user_dir,
                db_connection_string=self.database_url,
                llm_model_func=self.get_llm_model_func(),
                embedding_func=self.get_embedding_func(),
            )

            # Store instance
            self.instances[user_id] = rag
            print(f"Created LightRAG instance for user {user_id}")
            return rag
        except Exception as e:
            logger.error(f"Error creating LightRAG instance for user {user_id}: {e}")
            # If initialization fails, try fallback to basic initialization
            return self.create_instance_fallback(user_id)

    def create_instance_fallback(self, user_id: str) -> LightRAG:
        """
        Fallback method to create a LightRAG instance without async initialization

        This method is used as a fallback when async initialization fails.

        Args:
            user_id: The user ID

        Returns:
            A new LightRAG instance
        """
        logger.warning(f"Using fallback initialization for user {user_id}")

        # Create user directory if it doesn't exist
        user_dir = os.path.join(self.base_dir, user_id)
        os.makedirs(user_dir, exist_ok=True)

        # Initialize LightRAG with user-specific directory
        rag = LightRAG(
            working_dir=user_dir,
            llm_model_func=self.get_llm_model_func(),
            embedding_func=self.get_embedding_func(),
            # enable_llm_cache_for_entity_extract=True,
            kv_storage="PGKVStorage",
            doc_status_storage="PGDocStatusStorage",
            graph_storage="PGGraphStorage",
            vector_storage="PGVectorStorage",
            auto_manage_storages_states=False,
        )

        # Store instance
        self.instances[user_id] = rag
        return rag

    def cleanup_instance(self, user_id: str) -> bool:
        """
        Clean up resources for a LightRAG instance

        Args:
            user_id: The user ID

        Returns:
            True if successfully cleaned up, False otherwise
        """
        if user_id not in self.instances:
            logger.warning(f"No instance found for user {user_id} during cleanup")
            return False

        try:
            # Remove from instances dict
            instance = self.instances.pop(user_id)

            # Any additional cleanup that might be needed for the instance
            # For example, closing connections or releasing resources
            # This would depend on the LightRAG API

            logger.info(f"Cleaned up RAG instance for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error cleaning up instance for user {user_id}: {e}")
            return False

    def get_llm_model_func(self) -> Callable:
        """
        Get the LLM model function for LightRAG with OpenAI's multilingual models

        This function configures and returns the LLM model function for use with LightRAG.
        It uses OpenAI's GPT models which have strong multilingual capabilities.

        Returns:
            A callable function for LLM model completions
        """
        # Check if OpenAI API key is configured
        if "OPENAI_API_KEY" not in os.environ and LIGHTRAG_INSTALLED:
            logger.warning(
                "OPENAI_API_KEY not set in environment variables. Using mock LLM function."
            )

            # Return a mock function if no API key is available
            def mock_llm_model_func(prompt: str) -> str:
                return f"Mock response for: {prompt}"

            return mock_llm_model_func

        # Return the actual OpenAI gpt_4o_mini_complete function
        # This is a function from LightRAG that uses OpenAI's API
        # The function has multilingual capabilities
        logger.info("Using OpenAI GPT-4o mini for LLM completions")

        async def my_llm_model_func(
            prompt: str,
            **kwargs: Any,
        ) -> str:
            return await gpt_4o_mini_complete(
                prompt=prompt,
                base_url="https://api.openai.com/v1",
                api_key=os.getenv("OPENAI_API_KEY"),
                **kwargs,
            )

        return my_llm_model_func

    def get_embedding_func(self) -> EmbeddingFunc:
        """
        Get the embedding function for LightRAG using OpenAI's multilingual embedding model

        This function configures and returns an embedding function wrapped in LightRAG's
        EmbeddingFunc class. It uses OpenAI's text-embedding-3-large model which has
        excellent multilingual capabilities.

        Returns:
            An EmbeddingFunc instance configured for OpenAI embeddings
        """
        # Check if OpenAI API key is configured
        if "OPENAI_API_KEY" not in os.environ and LIGHTRAG_INSTALLED:
            logger.warning(
                "OPENAI_API_KEY not set in environment variables. Using mock embedding function."
            )

            # Return a mock function if no API key is available
            def mock_embedding_func(text: str) -> list:
                return [0.0] * VECTOR_DIMENSION

            return EmbeddingFunc(
                embedding_dim=VECTOR_DIMENSION,
                max_token_size=MAX_TOKEN_SIZE,
                func=mock_embedding_func,
            )

        logger.info(f"Using OpenAI embeddings with dimension={VECTOR_DIMENSION}")

        # Return the actual OpenAI embedding function wrapped in EmbeddingFunc
        # The OpenAI embedding models have strong multilingual capabilities
        return EmbeddingFunc(
            embedding_dim=VECTOR_DIMENSION,  # 1536 for text-embedding-3-large
            max_token_size=MAX_TOKEN_SIZE,  # 8192 as specified in the PRD
            func=openai_embed,
        )


class LRURAGManager(RAGInstanceManager):
    """
    RAG Instance Manager with LRU (Least Recently Used) caching to limit memory usage
    """

    def __init__(self, base_dir: str, database_url: str, max_instances: int = 100):
        """
        Initialize the LRU RAG instance manager

        Args:
            base_dir: The base directory for user data
            database_url: The database connection string
            max_instances: Maximum number of instances to keep in memory
        """
        super().__init__(base_dir, database_url, max_instances)
        self.lru_order = []

        logger.info(f"Initialized LRURAGManager with max_instances={max_instances}")

    def get_instance(self, user_id: str) -> LightRAG:
        """
        Get or create a LightRAG instance with LRU caching

        Args:
            user_id: The user ID

        Returns:
            A LightRAG instance
        """
        if user_id in self.instances:
            # Move to the end of LRU list (most recently used)
            if user_id in self.lru_order:
                self.lru_order.remove(user_id)
            self.lru_order.append(user_id)
            return self.instances[user_id]

        # If we're at capacity, remove least recently used instance
        if len(self.instances) >= self.max_instances and self.lru_order:
            lru_user = self.lru_order.pop(0)
            self.cleanup_instance(lru_user)

        # Create new instance
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        rag = loop.run_until_complete(self.create_instance_async(user_id))

        self.lru_order.append(user_id)
        return rag


# Singleton manager instance
_manager = None


def get_rag_manager(
    base_dir: str = DATA_DIR, database_url: Optional[str] = None, use_lru: bool = True
) -> RAGInstanceManager:
    """
    Get or create the RAG instance manager singleton

    Args:
        base_dir: The base directory for user data
        database_url: The database connection string
        use_lru: Whether to use LRU caching (True for LRURAGManager, False for RAGInstanceManager)

    Returns:
        The RAG instance manager singleton
    """
    global _manager
    if _manager is None:
        from app.config import DATABASE_URL

        db_url = database_url or DATABASE_URL
        if use_lru:
            _manager = LRURAGManager(base_dir, db_url)
        else:
            _manager = RAGInstanceManager(base_dir, db_url)

    return _manager
