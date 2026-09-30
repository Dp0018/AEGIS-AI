import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.document import DocumentStatus

class DocumentResponse(BaseModel):
    """Pydantic schema representing the document details returned in API responses."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    content_type: str
    file_size: int
    status: DocumentStatus
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
