from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base

class Message(Base):
    """SQLAlchemy model representing a chat message in a conversation thread."""
    __tablename__ = "messages"

    thread_id = Column(UUID(as_uuid=True), ForeignKey("threads.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)  # "user", "assistant", "system", "human_feedback"
    content = Column(Text, nullable=False)

    # Relationships
    thread = relationship("Thread", back_populates="messages")
