import uuid
from typing import AsyncGenerator, List, Optional
import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import get_db_session
from app.db.redis import get_redis
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.repositories.audit import AuditLogRepository
from app.repositories.document import DocumentRepository
from app.services.auth import AuthService
from app.services.document import DocumentService
from app.services.rag import RAGService
from app.services.agent import AgentService
from app.repositories.thread import ThreadRepository
from app.repositories.memory import MemoryRepository
from app.services.memory import MemoryService

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_PREFIX}/auth/token"
)


async def get_user_repository(db: AsyncSession = Depends(get_db_session)) -> UserRepository:
    """Dependency producing UserRepository instance."""
    return UserRepository(db)

async def get_audit_repository(db: AsyncSession = Depends(get_db_session)) -> AuditLogRepository:
    """Dependency producing AuditLogRepository instance."""
    return AuditLogRepository(db)

async def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    audit_repo: AuditLogRepository = Depends(get_audit_repository),
    redis: aioredis.Redis = Depends(get_redis)
) -> AuthService:
    """Dependency producing AuthService instance."""
    return AuthService(user_repo, audit_repo, redis)

async def get_document_repository(db: AsyncSession = Depends(get_db_session)) -> DocumentRepository:
    """Dependency producing DocumentRepository instance."""
    return DocumentRepository(db)

async def get_document_service(
    doc_repo: DocumentRepository = Depends(get_document_repository),
    audit_repo: AuditLogRepository = Depends(get_audit_repository)
) -> DocumentService:
    """Dependency producing DocumentService instance."""
    return DocumentService(doc_repo, audit_repo)

async def get_rag_service(
    doc_service: DocumentService = Depends(get_document_service)
) -> RAGService:
    """Dependency producing RAGService instance."""
    return RAGService(doc_service)

async def get_thread_repository(db: AsyncSession = Depends(get_db_session)) -> ThreadRepository:
    """Dependency producing ThreadRepository instance."""
    return ThreadRepository(db)

async def get_memory_repository(db: AsyncSession = Depends(get_db_session)) -> MemoryRepository:
    """Dependency producing MemoryRepository instance."""
    return MemoryRepository(db)

async def get_memory_service(
    thread_repo: ThreadRepository = Depends(get_thread_repository),
    memory_repo: MemoryRepository = Depends(get_memory_repository)
) -> MemoryService:
    """Dependency producing MemoryService instance."""
    return MemoryService(thread_repo, memory_repo)

async def get_agent_service(
    rag_service: RAGService = Depends(get_rag_service),
    thread_repo: ThreadRepository = Depends(get_thread_repository)
) -> AgentService:
    """Dependency producing AgentService instance."""
    return AgentService(rag_service, thread_repo)



async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: UserRepository = Depends(get_user_repository),
    redis: aioredis.Redis = Depends(get_redis)
) -> User:
    """Resolve, decode, and validate the active JWT authorization access token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_token(token, settings.JWT_SECRET_KEY)
        token_type = payload.get("type")
        if token_type != "access":
            raise credentials_exception
            
        subject: Optional[str] = payload.get("sub")
        jti: Optional[str] = payload.get("jti")
        if not subject or not jti:
            raise credentials_exception
            
    except jwt.PyJWTError:
        raise credentials_exception

    # Check if access token jti is blacklisted in Redis
    is_blacklisted = await redis.exists(f"blacklist:{jti}")
    if is_blacklisted:
        raise credentials_exception

    user_id = uuid.UUID(subject)
    user = await user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise credentials_exception
        
    return user

class RoleChecker:
    """FastAPI dependency to validate user roles for RBAC control."""

    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for this role"
            )
        return current_user

# Expose role dependency checkers
get_admin_user = RoleChecker([UserRole.ADMIN])
get_operator_user = RoleChecker([UserRole.ADMIN, UserRole.OPERATOR])
get_viewer_user = RoleChecker([UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER])
