import uuid
from typing import List, Optional
from pydantic import BaseModel, Field

class RAGRetrieveRequest(BaseModel):
    """Pydantic request body for RAG retrieve context endpoints."""
    query: str = Field(..., description="The query string to match context for")
    top_k: int = Field(5, ge=1, le=20, description="Number of context documents to retrieve")
    document_ids: Optional[List[uuid.UUID]] = Field(None, description="Optional document ID filters")

class RAGRetrieveResponse(BaseModel):
    """Pydantic schema representing a single retrieved text chunk match."""
    text: str = Field(..., description="The text content of the matching chunk")
    filename: str = Field(..., description="The filename of the source document")
    score: float = Field(..., description="Similarity confidence score")
    document_id: uuid.UUID = Field(..., description="UUID of the parent document")
