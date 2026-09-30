import uuid
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog

class AuditLogRepository:
    """Repository class managing audit logging operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: Optional[uuid.UUID],
        action: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
        payload: Optional[Dict[str, Any]]
    ) -> AuditLog:
        """Create and persist a new security/audit log entry."""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            payload=payload
        )
        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)
        return audit_log
