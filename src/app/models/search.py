from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, conint, confloat, model_validator
import logging

logger = logging.getLogger(__name__)


class SearchRequest(BaseModel):
    """Request model for vector similarity search"""

    query: str = Field(..., min_length=1, description="The search query text")
    max_chunks: Optional[conint(ge=1, le=20)] = Field(
        5, description="Maximum number of chunks to retrieve (1-20)"
    )
    threshold: Optional[confloat(ge=0.0, le=1.0)] = Field(
        0.7, description="Similarity threshold (0.0-1.0)"
    )
    mode: Optional[str] = Field(
        "hybrid",
        description="Search mode: 'naive', 'local', 'global', 'hybrid', or 'mix'",
    )

    @model_validator(mode="after")
    def validate_mode(self):
        valid_modes = ["naive", "local", "global", "hybrid", "mix"]
        if self.mode not in valid_modes:
            logger.warning(f"Invalid mode: {self.mode}. Defaulting to 'hybrid'")
            self.mode = "hybrid"
        return self


class SearchResult(BaseModel):
    """Model for a single search result chunk"""

    text: str = Field(..., description="Content of the matched chunk")
    similarity: float = Field(..., description="Similarity score (0.0-1.0)")
    document_id: str = Field(..., description="ID of the source document")
    document_title: Optional[str] = Field(
        None, description="Title of the source document"
    )
    chunk_id: str = Field(..., description="Chunk identifier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class SearchResponse(BaseModel):
    """Response model for search endpoint"""

    results: List[SearchResult] = Field(..., description="Search results")
    total: int = Field(..., description="Total number of results")
    query: str = Field(..., description="Original query text")
    elapsed_time: Optional[float] = Field(
        None, description="Query execution time in seconds"
    )


class QueryRequest(BaseModel):
    """Request model for RAG-powered query"""

    query: str = Field(..., min_length=1, description="The query text")
    max_chunks: Optional[conint(ge=1, le=20)] = Field(
        5, description="Maximum number of chunks to retrieve (1-20)"
    )
    mode: Optional[str] = Field(
        "hybrid",
        description="Search mode: 'naive', 'local', 'global', 'hybrid', or 'mix'",
    )

    @model_validator(mode="after")
    def validate_mode(self):
        valid_modes = ["naive", "local", "global", "hybrid", "mix"]
        if self.mode not in valid_modes:
            logger.warning(f"Invalid mode: {self.mode}. Defaulting to 'hybrid'")
            self.mode = "hybrid"
        return self


class QueryResponse(BaseModel):
    """Response model for query endpoint"""

    answer: str = Field(..., description="Generated answer text")
    sources: List[SearchResult] = Field(
        ..., description="Source chunks used to generate the answer"
    )
    query: str = Field(..., description="Original query text")
    elapsed_time: Optional[float] = Field(
        None, description="Query execution time in seconds"
    )
    confidence: Optional[float] = Field(
        None, description="Confidence score (if available)"
    )
