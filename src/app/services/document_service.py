"""
Document service for managing user documents with LightRAG
"""

import os
import asyncio
import logging
from typing import List, Optional, Dict, Any, BinaryIO
from datetime import datetime
from uuid import UUID, uuid4
import shutil
import json
from fastapi import UploadFile, HTTPException, status

from app.config import DATA_DIR
from app.services.rag_manager import get_rag_manager
from app.utilities.lightrag_utils import ingest_document

logger = logging.getLogger(__name__)

# Valid document MIME types that can be processed
VALID_MIME_TYPES = [
    "text/plain",
    "text/markdown",
    "application/pdf",
    "application/json",
    "text/csv",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/msword",  # .doc
]

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


class DocumentService:
    """Service for managing document operations"""

    @staticmethod
    def get_user_docs_dir(user_id: str) -> str:
        """Get the user's documents directory"""
        user_dir = os.path.join(DATA_DIR, user_id)
        docs_dir = os.path.join(user_dir, "documents")
        os.makedirs(docs_dir, exist_ok=True)
        return docs_dir

    @staticmethod
    def get_user_meta_path(user_id: str) -> str:
        """Get the path to the user's document metadata file"""
        docs_dir = DocumentService.get_user_docs_dir(user_id)
        return os.path.join(docs_dir, "metadata.json")

    @staticmethod
    def _validate_file(file: UploadFile) -> None:
        """
        Validate file before processing

        Args:
            file: The uploaded file

        Raises:
            HTTPException: If the file is invalid
        """
        # Check file size (this is not perfect as it's in memory)
        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds the maximum limit of {MAX_FILE_SIZE} bytes",
            )

        # Check content type
        content_type = file.content_type
        if content_type not in VALID_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type: {content_type}. Supported types: {VALID_MIME_TYPES}",
            )

    @staticmethod
    async def load_metadata(user_id: str) -> Dict[str, Dict[str, Any]]:
        """
        Load document metadata for a user

        Args:
            user_id: The user ID

        Returns:
            Dictionary of document metadata
        """
        meta_path = DocumentService.get_user_meta_path(user_id)

        if not os.path.exists(meta_path):
            return {}

        try:
            with open(meta_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading metadata for user {user_id}: {e}")
            return {}

    @staticmethod
    async def save_metadata(user_id: str, metadata: Dict[str, Dict[str, Any]]) -> None:
        """
        Save document metadata for a user

        Args:
            user_id: The user ID
            metadata: Dictionary of document metadata
        """
        meta_path = DocumentService.get_user_meta_path(user_id)

        try:
            with open(meta_path, "w") as f:
                json.dump(metadata, f, default=str)
        except Exception as e:
            logger.error(f"Error saving metadata for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save document metadata",
            )

    @staticmethod
    async def upload_document(
        user_id: str,
        file: UploadFile,
        title: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Upload and process a document for a user

        Args:
            user_id: The user ID
            file: The uploaded file
            title: Document title
            description: Optional document description
            tags: Optional document tags

        Returns:
            Document metadata
        """
        # Validate the file
        DocumentService._validate_file(file)

        # Generate a unique ID for the document
        doc_id = str(uuid4())

        # Get the user's documents directory
        docs_dir = DocumentService.get_user_docs_dir(user_id)

        # Define file paths
        file_path = os.path.join(docs_dir, f"{doc_id}_{file.filename}")

        # Save file metadata
        now = datetime.utcnow()
        metadata = {
            "id": doc_id,
            "user_id": user_id,
            "title": title,
            "description": description or "",
            "filename": file.filename,
            "file_size": file.size or 0,
            "mime_type": file.content_type,
            "created_at": now,
            "updated_at": now,
            "tags": tags or [],
            "status": "uploading",
            "file_path": file_path,
        }

        # Load existing metadata
        all_metadata = await DocumentService.load_metadata(user_id)
        all_metadata[doc_id] = metadata

        # Save updated metadata
        await DocumentService.save_metadata(user_id, all_metadata)

        try:
            # Save the file to disk
            with open(file_path, "wb") as f:
                # Read file in chunks to avoid memory issues
                content = await file.read()
                f.write(content)

            # Update status
            metadata["status"] = "processing"
            all_metadata[doc_id] = metadata
            await DocumentService.save_metadata(user_id, all_metadata)

            # Process with LightRAG in the background
            asyncio.create_task(
                DocumentService._process_document(
                    user_id, doc_id, file_path, content.decode("utf-8", errors="ignore")
                )
            )

            # Return metadata without internal fields
            response_metadata = metadata.copy()
            response_metadata.pop("file_path", None)
            return response_metadata

        except Exception as e:
            logger.error(f"Error uploading document for user {user_id}: {e}")

            # Update status to failed
            if doc_id in all_metadata:
                all_metadata[doc_id]["status"] = "failed"
                await DocumentService.save_metadata(user_id, all_metadata)

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload document: {str(e)}",
            )

    @staticmethod
    async def _process_document(
        user_id: str, doc_id: str, file_path: str, content: str
    ) -> None:
        """
        Process a document with LightRAG

        Args:
            user_id: The user ID
            doc_id: The document ID
            file_path: Path to the document file
            content: Document content
        """
        try:
            # Get the RAG instance for the user
            rag_manager = get_rag_manager()
            rag = rag_manager.get_instance(user_id)

            # Ingest the document into LightRAG
            await ingest_document(rag, content, doc_id, file_path)

            # Update status to completed
            all_metadata = await DocumentService.load_metadata(user_id)
            if doc_id in all_metadata:
                all_metadata[doc_id]["status"] = "complete"
                await DocumentService.save_metadata(user_id, all_metadata)

            logger.info(f"Document {doc_id} processed successfully for user {user_id}")

        except Exception as e:
            logger.error(f"Error processing document {doc_id} for user {user_id}: {e}")

            # Update status to failed
            all_metadata = await DocumentService.load_metadata(user_id)
            if doc_id in all_metadata:
                all_metadata[doc_id]["status"] = "failed"
                await DocumentService.save_metadata(user_id, all_metadata)

    @staticmethod
    async def get_documents(user_id: str) -> List[Dict[str, Any]]:
        """
        Get all documents for a user

        Args:
            user_id: The user ID

        Returns:
            List of document metadata
        """
        all_metadata = await DocumentService.load_metadata(user_id)

        # Return all documents without internal fields
        documents = []
        for doc_id, metadata in all_metadata.items():
            doc_metadata = metadata.copy()
            doc_metadata.pop("file_path", None)
            documents.append(doc_metadata)

        return documents

    @staticmethod
    async def get_document(user_id: str, doc_id: str) -> Dict[str, Any]:
        """
        Get document metadata by ID

        Args:
            user_id: The user ID
            doc_id: The document ID

        Returns:
            Document metadata

        Raises:
            HTTPException: If the document doesn't exist
        """
        all_metadata = await DocumentService.load_metadata(user_id)

        if doc_id not in all_metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found",
            )

        # Return document without internal fields
        metadata = all_metadata[doc_id].copy()
        metadata.pop("file_path", None)
        return metadata

    @staticmethod
    async def update_document(
        user_id: str,
        doc_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Update document metadata

        Args:
            user_id: The user ID
            doc_id: The document ID
            title: Optional new title
            description: Optional new description
            tags: Optional new tags

        Returns:
            Updated document metadata

        Raises:
            HTTPException: If the document doesn't exist
        """
        all_metadata = await DocumentService.load_metadata(user_id)

        if doc_id not in all_metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found",
            )

        # Update fields
        metadata = all_metadata[doc_id]
        if title is not None:
            metadata["title"] = title
        if description is not None:
            metadata["description"] = description
        if tags is not None:
            metadata["tags"] = tags

        # Update timestamp
        metadata["updated_at"] = datetime.utcnow()

        # Save updated metadata
        await DocumentService.save_metadata(user_id, all_metadata)

        # Return updated metadata without internal fields
        response_metadata = metadata.copy()
        response_metadata.pop("file_path", None)
        return response_metadata

    @staticmethod
    async def delete_document(user_id: str, doc_id: str) -> Dict[str, Any]:
        """
        Delete a document

        Args:
            user_id: The user ID
            doc_id: The document ID

        Returns:
            Deletion status

        Raises:
            HTTPException: If the document doesn't exist
        """
        all_metadata = await DocumentService.load_metadata(user_id)

        if doc_id not in all_metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found",
            )

        # Get file path before removing metadata
        file_path = all_metadata[doc_id].get("file_path")

        # Remove from metadata
        metadata = all_metadata.pop(doc_id)
        await DocumentService.save_metadata(user_id, all_metadata)

        # Delete file if it exists
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.error(f"Error deleting file {file_path}: {e}")

        # TODO: Remove from LightRAG index (when LightRAG supports document deletion)

        return {
            "id": doc_id,
            "success": True,
            "message": "Document deleted successfully",
        }
