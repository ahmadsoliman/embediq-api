from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import logging
import time
from lightrag import LightRAG, QueryParam

from app.dependencies import get_rag_for_user
from app.models.search import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    QueryRequest,
    QueryResponse,
)
from app.utilities.lightrag_utils import query_lightrag, search_lightrag

logger = logging.getLogger(__name__)

# Create search router
search_router = APIRouter(tags=["search"])


@search_router.post(
    "/search",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Vector similarity search",
    description="Perform vector similarity search on the user's documents",
)
async def search(request: SearchRequest, rag: LightRAG = Depends(get_rag_for_user)):
    """
    Perform vector similarity search on the user's documents

    This endpoint allows users to search their documents using vector similarity.
    The search is performed on the user-specific LightRAG instance.
    """
    logger.info(
        f"Search request: query='{request.query}', max_chunks={request.max_chunks}"
    )

    try:
        # Start timer
        start_time = time.time()

        # Use the search_lightrag helper function to handle the search operation
        search_results = await search_lightrag(
            rag=rag,
            query=request.query,
            mode=request.mode,
            max_chunks=request.max_chunks,
        )

        # Calculate elapsed time
        elapsed_time = time.time() - start_time

        # Transform results to response model
        results = []
        for result in search_results:
            # Apply threshold filtering if necessary
            similarity = result.get("similarity", 0.0)
            if similarity >= request.threshold:
                search_result = SearchResult(
                    text=result.get("text", ""),
                    similarity=similarity,
                    document_id=result.get("document_id", ""),
                    document_title=result.get("document_title", ""),
                    chunk_id=result.get("chunk_id", ""),
                    metadata=result.get("metadata", {}),
                )
                results.append(search_result)

        # Create response
        response = SearchResponse(
            results=results,
            total=len(results),
            query=request.query,
            elapsed_time=elapsed_time,
        )

        logger.info(
            f"Search completed in {elapsed_time:.2f}s with {len(results)} results"
        )
        return response

    except Exception as e:
        logger.error(f"Error performing search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search error: {str(e)}",
        )


@search_router.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="RAG-powered query",
    description="Perform a RAG-powered query on the user's documents",
)
async def query(request: QueryRequest, rag: LightRAG = Depends(get_rag_for_user)):
    """
    Perform a RAG-powered query on the user's documents

    This endpoint allows users to query their documents using RAG.
    The query combines vector search with generative responses.
    """
    logger.info(
        f"Query request: query='{request.query}', max_chunks={request.max_chunks}"
    )

    try:
        # Start timer
        start_time = time.time()

        # Perform query using LightRAG
        response = await query_lightrag(
            rag=rag,
            query=request.query,
            mode=request.mode,
            max_chunks=request.max_chunks,
        )

        # Calculate elapsed time
        elapsed_time = time.time() - start_time

        # Transform search results to response model
        sources = []
        for chunk in getattr(response, "chunks", []):
            search_result = SearchResult(
                text=chunk.get("text", ""),
                similarity=chunk.get("similarity", 0.0),
                document_id=chunk.get("document_id", ""),
                document_title=chunk.get("document_title", ""),
                chunk_id=chunk.get("chunk_id", ""),
                metadata=chunk.get("metadata", {}),
            )
            sources.append(search_result)

        # Create response
        query_response = QueryResponse(
            answer=getattr(response, "response", str(response)),
            sources=sources,
            query=request.query,
            elapsed_time=elapsed_time,
            confidence=getattr(response, "confidence", None),
        )

        logger.info(f"Query completed in {elapsed_time:.2f}s")
        return query_response

    except Exception as e:
        logger.error(f"Error performing query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query error: {str(e)}",
        )
