"""
Utilities for working with LightRAG instances
"""

import os
import logging
import asyncio
import time
from typing import Optional, Callable, Dict, Any

from app.config import (
    VECTOR_DIMENSION,
    MAX_TOKEN_SIZE,
    CHUNK_SIZE,
    GRAPH_TRAVERSAL_DEPTH,
    CACHE_ENABLED,
    CACHE_SIZE,
)
from app.monitoring.lightrag_monitor import (
    monitor_lightrag_operation,
    get_lightrag_monitor,
)

logger = logging.getLogger(__name__)

# Check if LightRAG is installed
try:
    from lightrag import LightRAG, QueryParam
    from lightrag.utils import EmbeddingFunc
    from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
    from lightrag.kg.shared_storage import initialize_pipeline_status

    LIGHTRAG_INSTALLED = True
except ImportError:
    logger.warning("LightRAG not installed. Using mock implementations.")
    LIGHTRAG_INSTALLED = False

    # Create mock classes and functions for testing without LightRAG
    class QueryParam:
        def __init__(self, mode="naive", top_k=5, **kwargs):
            self.mode = mode
            self.top_k = top_k
            self.kwargs = kwargs

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

        async def initialize_storages(self):
            logger.info("Mock: Initialized storages")

        def insert(self, text):
            logger.info(f"Mock: Inserted text of length {len(text)}")

        async def ainsert(self, text, **kwargs):
            # Accept any keyword arguments (chunk_size, chunk_overlap, etc.)
            logger.info(f"Mock: Asynchronously inserted text of length {len(text)}")

        def search(self, query_text, param=None):
            logger.info(f"Mock: Searched with text: {query_text}")
            return [
                {
                    "text": f"Mock search result for: {query_text}",
                    "similarity": 0.85,
                    "document_id": "mock-doc-123",
                    "document_title": "Mock Document",
                    "chunk_id": "mock-chunk-123",
                    "metadata": {"page": 1},
                }
            ]

        async def asearch(self, query_text, param=None):
            logger.info(f"Mock: Asynchronously searched with text: {query_text}")
            return self.search(query_text, param)

        def query(self, query_text, param=None):
            logger.info(f"Mock: Queried with text: {query_text}")
            result = type(
                "obj",
                (object,),
                {
                    "response": f"Mock response for: {query_text}",
                    "confidence": 0.92,
                    "chunks": self.search(query_text, param),
                },
            )
            return result

        async def aquery(self, query_text, param=None):
            logger.info(f"Mock: Asynchronously queried with text: {query_text}")
            return self.query(query_text, param)

    class EmbeddingFunc:
        def __init__(self, embedding_dim=None, max_token_size=None, func=None):
            self.embedding_dim = embedding_dim
            self.max_token_size = max_token_size
            self.func = func

    # Mock OpenAI functions
    async def initialize_pipeline_status():
        logger.info("Mock: Initialized pipeline status")

    def gpt_4o_mini_complete(*args, **kwargs):
        return "Mock GPT-4o mini response"

    def openai_embed(texts):
        # Return an array of the correct dimension for each text
        return [
            [0.0] * VECTOR_DIMENSION
            for _ in range(len(texts) if isinstance(texts, list) else 1)
        ]


async def initialize_lightrag_instance(
    working_dir: str,
    db_connection_string: Optional[str] = None,
    llm_model_func: Optional[Callable] = None,
    embedding_func: Optional[EmbeddingFunc] = None,
) -> LightRAG:
    """
    Initialize a LightRAG instance asynchronously

    This function initializes a LightRAG instance with the given parameters,
    including proper initialization of storages and pipeline status.

    Args:
        working_dir: The working directory for LightRAG
        db_connection_string: The database connection string
        llm_model_func: The LLM model function to use (default: gpt_4o_mini_complete)
        embedding_func: The embedding function to use (default: OpenAI multilingual embeddings)

    Returns:
        An initialized LightRAG instance
    """
    # Create directory if it doesn't exist
    os.makedirs(working_dir, exist_ok=True)

    # Use default functions if not provided
    if llm_model_func is None:
        llm_model_func = gpt_4o_mini_complete

    if embedding_func is None:
        embedding_func = EmbeddingFunc(
            embedding_dim=VECTOR_DIMENSION,
            max_token_size=MAX_TOKEN_SIZE,
            func=openai_embed,
        )

    # Initialize LightRAG
    rag = LightRAG(
        working_dir=working_dir,
        llm_model_func=llm_model_func,
        embedding_func=embedding_func,
        enable_llm_cache_for_entity_extract=True,
        kv_storage="PGKVStorage",
        doc_status_storage="PGDocStatusStorage",
        graph_storage="PGGraphStorage",
        vector_storage="PGVectorStorage",
        auto_manage_storages_states=False,
    )

    # Initialize storages and pipeline status
    if LIGHTRAG_INSTALLED:
        try:
            logger.info(f"Initializing LightRAG storages in {working_dir}")
            await rag.initialize_storages()
            await initialize_pipeline_status()

            # Set embedding function for graph database
            rag.chunk_entity_relation_graph.embedding_func = embedding_func

            logger.info("LightRAG initialization complete")
        except Exception as e:
            logger.error(f"Error initializing LightRAG: {e}")
            raise

    return rag


@monitor_lightrag_operation("insert")
async def ingest_document(
    rag: LightRAG, content: str, documentId: str, file_path: str = None
) -> None:
    """
    Ingest a document into LightRAG

    Args:
        rag: The LightRAG instance
        content: The document content
        documentId: The document ID
        file_path: Optional file path for the document
    """
    try:
        if not documentId:
            raise ValueError("documentId is required")

        if not file_path:
            file_path = documentId

        # Apply configuration parameters
        chunk_size = CHUNK_SIZE

        if hasattr(rag, "ainsert"):
            logger.info("Using async insert")
            # Use async insert if available
            await rag.ainsert(
                content,
                ids=[str(documentId)],
                file_paths=[str(file_path)],
                chunk_size=chunk_size,
            )
        else:
            logger.info("Using sync insert")
            # Fall back to sync insert
            # Note: In a real async context, this blocks the event loop
            rag.insert(
                content,
                ids=[str(documentId)],
                file_paths=[str(file_path)],
                chunk_size=chunk_size,
            )

        logger.info(f"Successfully ingested document of length {len(content)}")
    except Exception as e:
        logger.error(f"Error ingesting document: {e}")
        # Record error in monitor
        monitor = get_lightrag_monitor()
        monitor.record_error()
        raise


@monitor_lightrag_operation("search")
async def search_lightrag(
    rag: LightRAG, query: str, mode: str = "hybrid", max_chunks: int = 5
) -> list:
    """
    Perform vector similarity search with a LightRAG instance

    Args:
        rag: The LightRAG instance
        query: The search query text
        mode: The search mode (naive, local, global, hybrid, mix)
        max_chunks: Maximum number of chunks to retrieve

    Returns:
        List of search results
    """
    try:
        # Apply configuration parameters
        param = QueryParam(
            mode=mode,
            top_k=max_chunks,
            chunk_size=CHUNK_SIZE,
            max_depth=GRAPH_TRAVERSAL_DEPTH,
        )

        if hasattr(rag, "asearch"):
            # Use async search if available
            results = await rag.asearch(query, param=param)
        else:
            # Fall back to sync search
            # Note: In a real async context, this blocks the event loop
            results = rag.search(query, param=param)

        logger.info(f"Search successful: {query}, found {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"Error searching with LightRAG: {e}")
        # Record error in monitor
        monitor = get_lightrag_monitor()
        monitor.record_error()
        raise


@monitor_lightrag_operation("query")
async def query_lightrag(
    rag: LightRAG, query: str, mode: str = "hybrid", max_chunks: int = 5
) -> str:
    """
    Query a LightRAG instance

    Args:
        rag: The LightRAG instance
        query: The query text
        mode: The query mode (naive, local, global, hybrid, mix)
        max_chunks: Maximum number of chunks to retrieve

    Returns:
        The query response
    """
    try:
        # Apply configuration parameters
        param = QueryParam(
            mode=mode,
            top_k=max_chunks,
            chunk_size=CHUNK_SIZE,
            max_depth=GRAPH_TRAVERSAL_DEPTH,
            use_cache=CACHE_ENABLED,
            cache_size=CACHE_SIZE,
        )

        if hasattr(rag, "aquery"):
            # Use async query if available
            response = await rag.aquery(query, param=param)
        else:
            # Fall back to sync query
            # Note: In a real async context, this blocks the event loop
            response = rag.query(query, param=param)

        logger.info(f"Query successful: {query}")
        return response
    except Exception as e:
        logger.error(f"Error querying LightRAG: {e}")
        # Record error in monitor
        monitor = get_lightrag_monitor()
        monitor.record_error()
        raise
