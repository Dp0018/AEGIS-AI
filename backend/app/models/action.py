from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.models.base import Base

class Action(Base):
    """SQLAlchemy model representing an execution tool action run during a thread."""
    __tablename__ = "actions"

    thread_id = Column(UUID(as_uuid=True), ForeignKey("threads.id", ondelete="CASCADE"), nullable=False)
    action_type = Column(String(100), nullable=False)  # "smtp_email_sent", "support_ticket_created"
    payload = Column(JSONB, nullable=False)

    # Relationships
    thread = relationship("Thread", back_populates="actions")
