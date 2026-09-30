from typing import Optional
from pydantic import BaseModel, Field, EmailStr

class CustomerLookupRequest(BaseModel):
    """Request schema to lookup a customer profile in CRM."""
    email: EmailStr = Field(..., description="The email address of the customer to query")

class TicketCreateRequest(BaseModel):
    """Request schema to create a support escalation ticket."""
    email: EmailStr = Field(..., description="The email address of the customer reporting the issue")
    issue: str = Field(..., min_length=5, description="Description of the customer issue/request")
    priority: Optional[str] = Field("medium", description="Priority level: low, medium, high")

class EmailSendRequest(BaseModel):
    """Request schema to send a simulated email."""
    to_email: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., min_length=1, description="Subject of the email")
    body: str = Field(..., min_length=1, description="Body content of the email")
