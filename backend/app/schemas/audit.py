import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class AuditLogResponse(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = Field(None, description="Initiating User UUID")
    action: str = Field(..., description="Action category logged")
    ip_address: Optional[str] = Field(None, description="IP address of source endpoint")
    user_agent: Optional[str] = Field(None, description="User Agent header value")
    payload: Optional[Dict[str, Any]] = Field(None, description="Metadata trace payload context")
    created_at: datetime

    class Config:
        from_attributes = True
