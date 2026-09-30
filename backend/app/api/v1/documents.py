import os
import uuid
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Request, status

from app.core.config import settings
from app.core.dependencies import get_document_repository, get_document_service, get_operator_user
from app.models.user import User
from app.repositories.document import DocumentRepository
from app.services.document import DocumentService
from app.schemas.document import DocumentResponse
from app.schemas.common import ErrorResponse

router = APIRouter()

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}

@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        415: {"model": ErrorResponse}
    }
)
async def upload_document(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_operator_user),
    doc_repo: DocumentRepository = Depends(get_document_repository),
    doc_service: DocumentService = Depends(get_document_service)
):
    """Upload a PDF, DOCX, or text/markdown document to the knowledge base.
    
    The file is saved, a database record created in 'pending' status, and
    parsing is queued to run in the background.
    """
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file format '{file.content_type}'. Allowed types are PDF, DOCX, TXT, and Markdown."
        )

    # 1. Create unique database record first
    db_doc = await doc_repo.create(
        filename=file.filename or "unnamed_document",
        content_type=file.content_type,
        file_size=0  # will update after saving
    )

    # 2. Save file on disk
    file_path = os.path.join(settings.UPLOAD_DIR, f"{db_doc.id}_{db_doc.filename}")
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Update file size in DB
        file_size = os.path.getsize(file_path)
        db_doc.file_size = file_size
        await doc_repo.db.commit()
        await doc_repo.db.refresh(db_doc)
        
    except Exception as e:
        # Cleanup DB record on filesystem save failure
        await doc_repo.delete(db_doc.id)
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to write uploaded file to disk: {str(e)}"
        )

    # 3. Queue parsing & indexing in background
    ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    background_tasks.add_task(
        doc_service.process_document,
        db_doc.id,
        file_path,
        ip_address=ip,
        user_agent=user_agent
    )

    return db_doc

@router.get(
    "/",
    response_model=List[DocumentResponse],
    responses={401: {"model": ErrorResponse}}
)
async def list_documents(
    current_user: User = Depends(get_operator_user),
    doc_repo: DocumentRepository = Depends(get_document_repository)
):
    """Retrieve metadata for all ingested documents."""
    return await doc_repo.list_all()

@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse}
    }
)
async def get_document_status(
    document_id: uuid.UUID,
    current_user: User = Depends(get_operator_user),
    doc_repo: DocumentRepository = Depends(get_document_repository)
):
    """Retrieve detailed processing status and metadata for a single document."""
    db_doc = await doc_repo.get_by_id(document_id)
    if not db_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return db_doc

@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse}
    }
)
async def delete_document(
    document_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_operator_user),
    doc_service: DocumentService = Depends(get_document_service)
):
    """Remove a document from database metadata, disk storage, and ChromaDB vector index."""
    ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    success = await doc_service.delete_document(
        document_id,
        ip_address=ip,
        user_agent=user_agent
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return {"detail": "Document successfully deleted"}
