import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.user import UserRole

class UserBase(BaseModel):
    email: EmailStr = Field(..., max_length=255, description="Unique primary email identifier")
    full_name: Optional[str] = Field(None, max_length=255, description="User full display name")
    role: UserRole = Field(UserRole.VIEWER, description="Assigned role for access permission check")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128, description="Plaintext raw user password")

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
