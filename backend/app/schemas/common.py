from pydantic import BaseModel, Field

class ErrorResponse(BaseModel):
    """Standardized API JSON exception format."""
    detail: str = Field(..., description="Error message description payload")
