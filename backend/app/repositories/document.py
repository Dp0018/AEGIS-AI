import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document, DocumentStatus

class DocumentRepository:
    """Repository class managing document database query/mutation operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, document_id: uuid.UUID) -> Optional[Document]:
        """Fetch a single document metadata record by UUID."""
        query = select(Document).where(Document.id == document_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_all(self) -> List[Document]:
        """List all document metadata records ordered by creation time descending."""
        query = select(Document).order_by(Document.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, filename: str, content_type: str, file_size: int) -> Document:
        """Create and persist a new Document metadata record in the database."""
        document = Document(
            filename=filename,
            content_type=content_type,
            file_size=file_size,
            status=DocumentStatus.PENDING
        )
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def update_status(
        self,
        document_id: uuid.UUID,
        status: DocumentStatus,
        error_message: Optional[str] = None
    ) -> Optional[Document]:
        """Update the processing status of a document."""
        document = await self.get_by_id(document_id)
        if not document:
            return None
        
        document.status = status
        document.error_message = error_message
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def delete(self, document_id: uuid.UUID) -> bool:
        """Delete a document metadata record from the database."""
        document = await self.get_by_id(document_id)
        if not document:
            return False
        
        await self.db.delete(document)
        await self.db.commit()
        return True
