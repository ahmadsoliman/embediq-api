"""
API routes for document management
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    File,
    UploadFile,
    Form,
    Query,
    Path,
)
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

from app.middleware.auth import validate_token
from app.models.documents import (
    DocumentCreate,
    DocumentResponse,
    DocumentList,
    DocumentUpdate,
    DocumentDeleteResponse,
)
from app.services.document_service import DocumentService

# Create documents router - remove the prefix since api_router already has it
documents_router = APIRouter(tags=["documents"])


@documents_router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a new document",
    description="Upload a new document for processing with LightRAG",
)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    user_id: str = Depends(validate_token),
):
    """
    Upload a new document for processing with LightRAG

    This endpoint allows users to upload documents to be processed by LightRAG.
    The document is stored in the user's directory and queued for processing.
    """
    # Add detailed logging
    logger = logging.getLogger(__name__)
    logger.info(
        f"Upload document request received: title={title}, file={file.filename}"
    )
    logger.info(f"File content type: {file.content_type}, size: {file.size}")
    logger.info(f"User ID: {user_id}")

    # Parse tags from string (comma-separated)
    tag_list = []
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        logger.info(f"Tags: {tag_list}")

    # Upload the document
    result = await DocumentService.upload_document(
        user_id=user_id,
        file=file,
        title=title,
        description=description,
        tags=tag_list,
    )

    # Return the document metadata
    logger.info(f"Document uploaded successfully with ID: {result.get('id')}")
    return result


@documents_router.get(
    "",
    response_model=DocumentList,
    status_code=status.HTTP_200_OK,
    summary="List all documents",
    description="List all documents for the authenticated user",
)
async def list_documents(
    user_id: str = Depends(validate_token),
    status_filter: Optional[str] = Query(
        None, description="Filter documents by status"
    ),
    tag: Optional[str] = Query(None, description="Filter documents by tag"),
):
    """
    List all documents for the authenticated user

    This endpoint lists all documents owned by the authenticated user.
    The results can be filtered by status or tag.
    """
    documents = await DocumentService.get_documents(user_id)

    # Apply filters if needed
    if status_filter:
        documents = [doc for doc in documents if doc.get("status") == status_filter]

    if tag:
        documents = [doc for doc in documents if tag in doc.get("tags", [])]

    return {
        "documents": documents,
        "total": len(documents),
    }


@documents_router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get document details",
    description="Get details for a specific document",
)
async def get_document(
    document_id: UUID = Path(..., description="Document ID"),
    user_id: str = Depends(validate_token),
):
    """
    Get details for a specific document

    This endpoint retrieves the details of a specific document owned by the authenticated user.
    """
    document = await DocumentService.get_document(user_id, str(document_id))
    return document


@documents_router.patch(
    "/{document_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update document details",
    description="Update metadata for a specific document",
)
async def update_document(
    update_data: DocumentUpdate,
    document_id: UUID = Path(..., description="Document ID"),
    user_id: str = Depends(validate_token),
):
    """
    Update metadata for a specific document

    This endpoint allows updating the metadata of a specific document owned by the authenticated user.
    """
    document = await DocumentService.update_document(
        user_id=user_id,
        doc_id=str(document_id),
        title=update_data.title,
        description=update_data.description,
        tags=update_data.tags,
    )
    return document


@documents_router.delete(
    "/{document_id}",
    response_model=DocumentDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a document",
    description="Delete a specific document",
)
async def delete_document(
    document_id: UUID = Path(..., description="Document ID"),
    user_id: str = Depends(validate_token),
):
    """
    Delete a specific document

    This endpoint deletes a specific document owned by the authenticated user.
    The document is removed from storage and its metadata is deleted.
    """
    result = await DocumentService.delete_document(user_id, str(document_id))
    return result
