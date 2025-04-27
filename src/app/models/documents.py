from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4


class DocumentBase(BaseModel):
    """Base model with common document fields"""

    title: str = Field(..., description="Document title")
    description: Optional[str] = Field(None, description="Document description")


class DocumentCreate(DocumentBase):
    """Model for document creation request"""

    tags: Optional[List[str]] = Field(
        default=[], description="List of tags for the document"
    )


class DocumentResponse(DocumentBase):
    """Model for document response"""

    id: UUID = Field(..., description="Document unique identifier")
    user_id: str = Field(..., description="ID of the user who owns the document")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type of the document")
    created_at: datetime = Field(..., description="Document creation timestamp")
    updated_at: datetime = Field(..., description="Document last update timestamp")
    tags: List[str] = Field(default=[], description="List of tags for the document")
    status: str = Field(..., description="Processing status of the document")


class DocumentList(BaseModel):
    """Model for document listing response"""

    documents: List[DocumentResponse] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents")


class DocumentUpdate(BaseModel):
    """Model for document update request"""

    title: Optional[str] = Field(None, description="Document title")
    description: Optional[str] = Field(None, description="Document description")
    tags: Optional[List[str]] = Field(None, description="List of tags for the document")


class DocumentDeleteResponse(BaseModel):
    """Model for document deletion response"""

    id: UUID = Field(..., description="ID of the deleted document")
    success: bool = Field(..., description="Whether the deletion was successful")
    message: str = Field(..., description="Status message")
