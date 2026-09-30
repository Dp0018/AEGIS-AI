import uuid
from typing import Optional
from pydantic import BaseModel, Field

class Token(BaseModel):
    access_token: str = Field(..., description="Access JWT token string")
    refresh_token: str = Field(..., description="Refresh JWT token string")
    token_type: str = Field("bearer", description="Token transfer category")

class TokenRefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh JWT token used to issue a new set of tokens")

class TokenPayload(BaseModel):
    sub: str = Field(..., description="Subject identity (User UUID)")
    role: Optional[str] = Field(None, description="User authorization role (Admin, Operator, Viewer)")
    exp: int = Field(..., description="Expiry epoch time")
    iat: int = Field(..., description="Issued at epoch time")
    jti: str = Field(..., description="Unique JWT token identifier")
    type: str = Field(..., description="JWT category validation flag (access or refresh)")
