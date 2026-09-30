from sqlalchemy import Column, String, Text
from app.models.base import Base

class Memory(Base):
    """SQLAlchemy model representing distilled profile memories of support customers."""
    __tablename__ = "memories"

    customer_email = Column(String(255), unique=True, index=True, nullable=False)
    summary = Column(Text, nullable=False)
