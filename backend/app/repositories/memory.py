from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import Memory

class MemoryRepository:
    """Repository handling SQL operations for profile Memory summaries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_memory_by_email(self, email: str) -> Optional[Memory]:
        """Fetch profile memory details by customer email."""
        result = await self.db.execute(
            select(Memory).where(Memory.customer_email == email.strip().lower())
        )
        return result.scalar_one_or_none()

    async def upsert_memory(self, email: str, summary: str) -> Memory:
        """Create new profile memory or update the existing summary for a customer."""
        clean_email = email.strip().lower()
        memory = await self.get_memory_by_email(clean_email)
        
        if memory:
            memory.summary = summary
        else:
            memory = Memory(customer_email=clean_email, summary=summary)
            self.db.add(memory)
            
        await self.db.commit()
        await self.db.refresh(memory)
        return memory
