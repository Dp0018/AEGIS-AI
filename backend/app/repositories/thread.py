import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.thread import Thread
from app.models.message import Message
from app.models.action import Action

class ThreadRepository:
    """Repository handling SQL operations for Threads, Messages, and Action logs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_thread(
        self,
        thread_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None
    ) -> Thread:
        """Resolve a Thread model by ID. Creates it if not present in the database."""
        result = await self.db.execute(select(Thread).where(Thread.id == thread_id))
        thread = result.scalar_one_or_none()
        
        if not thread:
            thread = Thread(id=thread_id, user_id=user_id)
            self.db.add(thread)
            await self.db.commit()
            await self.db.refresh(thread)
            
        return thread

    async def create_message(
        self,
        thread_id: uuid.UUID,
        role: str,
        content: str
    ) -> Message:
        """Create and persist a Message record in the database."""
        message = Message(thread_id=thread_id, role=role, content=content)
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        
        try:
            from app.core.kafka import publish_kafka_event
            payload = {
                "id": str(message.id),
                "thread_id": str(thread_id),
                "role": role,
                "content": content,
                "created_at": message.created_at.isoformat() if message.created_at else None
            }
            await publish_kafka_event("telemetry-events", str(thread_id), {
                "event_type": "message_created",
                "message": payload
            })
        except Exception:
            pass
            
        return message

    async def get_thread_messages(self, thread_id: uuid.UUID) -> List[Message]:
        """Fetch all messages associated with a thread sorted by created_at."""
        result = await self.db.execute(
            select(Message)
            .where(Message.thread_id == thread_id)
            .order_by(Message.created_at.asc())
        )
        return list(result.scalars().all())

    async def create_action(
        self,
        thread_id: uuid.UUID,
        action_type: str,
        payload: dict
    ) -> Action:
        """Log a tool execution action run during a thread."""
        action = Action(thread_id=thread_id, action_type=action_type, payload=payload)
        self.db.add(action)
        await self.db.commit()
        await self.db.refresh(action)
        
        try:
            from app.core.kafka import publish_kafka_event
            action_payload = {
                "id": str(action.id),
                "thread_id": str(thread_id),
                "action_type": action_type,
                "payload": payload,
                "created_at": action.created_at.isoformat() if action.created_at else None
            }
            await publish_kafka_event("telemetry-events", str(thread_id), {
                "event_type": "action_created",
                "action": action_payload
            })
        except Exception:
            pass
            
        return action

    async def get_thread_actions(self, thread_id: uuid.UUID) -> List[Action]:
        """Fetch all action logs associated with a thread."""
        result = await self.db.execute(
            select(Action)
            .where(Action.thread_id == thread_id)
            .order_by(Action.created_at.asc())
        )
        return list(result.scalars().all())

    async def list_all_threads(self) -> List[Thread]:
        """Fetch all conversation threads sorted by updated_at descending."""
        result = await self.db.execute(
            select(Thread).order_by(Thread.updated_at.desc())
        )
        return list(result.scalars().all())
