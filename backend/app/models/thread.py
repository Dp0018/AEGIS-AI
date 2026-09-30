from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base

class Thread(Base):
    """SQLAlchemy model representing a conversation/agent session thread."""
    __tablename__ = "threads"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    user = relationship("User", backref="threads")
    messages = relationship("Message", back_populates="thread", cascade="all, delete-orphan")
    actions = relationship("Action", back_populates="thread", cascade="all, delete-orphan")
