import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.repositories.audit import AuditLogRepository
from app.schemas.user import UserCreate
from app.schemas.token import Token, TokenPayload
import jwt

class AuthService:
    """Service layer handling user lifecycle, authentication, token rotation, and logging."""

    def __init__(
        self,
        user_repo: UserRepository,
        audit_repo: AuditLogRepository,
        redis_client: aioredis.Redis
    ):
        self.user_repo = user_repo
        self.audit_repo = audit_repo
        self.redis = redis_client

    async def register_user(
        self,
        user_in: UserCreate,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> User:
        """Register a new user. Performs email validation and admin bootstrapping."""
        existing_user = await self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise ValueError("Email already registered")

        # Admin Bootstrapping
        user_count = await self.user_repo.count()
        if user_count == 0:
            user_in.role = UserRole.ADMIN

        hashed_password = get_password_hash(user_in.password)
        user = await self.user_repo.create(user_in, hashed_password)

        await self.audit_repo.create(
            user_id=user.id,
            action="user_registered",
            ip_address=ip_address,
            user_agent=user_agent,
            payload={"email": user.email, "role": user.role}
        )
        return user

    async def authenticate_user(
        self,
        email: str,
        plain_password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> User:
        """Authenticate user credentials. Throws ValueError on failures."""
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(plain_password, user.hashed_password):
            await self.audit_repo.create(
                user_id=None,
                action="login_failed",
                ip_address=ip_address,
                user_agent=user_agent,
                payload={"email": email, "reason": "Invalid credentials"}
            )
            raise ValueError("Invalid email or password")

        if not user.is_active:
            await self.audit_repo.create(
                user_id=user.id,
                action="login_failed",
                ip_address=ip_address,
                user_agent=user_agent,
                payload={"email": email, "reason": "Account is inactive"}
            )
            raise ValueError("User account is inactive")

        await self.audit_repo.create(
            user_id=user.id,
            action="login_success",
            ip_address=ip_address,
            user_agent=user_agent,
            payload={}
        )
        return user

    async def create_tokens_for_user(self, user: User) -> Token:
        """Create access and refresh token pair for a validated user."""
        subject = str(user.id)
        access_token = create_access_token(subject=subject, role=user.role.value)
        refresh_token = create_refresh_token(subject=subject)
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

    async def refresh_access_token(
        self,
        refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Token:
        """Execute Refresh Token Rotation. Invalidates old refresh token, yields new pair."""
        try:
            payload = decode_token(refresh_token, settings.JWT_REFRESH_SECRET_KEY)
            token_type = payload.get("type")
            if token_type != "refresh":
                raise ValueError("Invalid token type")
        except jwt.PyJWTError:
            raise ValueError("Invalid or expired refresh token")

        jti = payload.get("jti")
        if not jti:
            raise ValueError("Invalid token identifier")

        # Check if blacklisted in Redis
        is_blacklisted = await self.redis.exists(f"blacklist:{jti}")
        if is_blacklisted:
            # Token replay attack suspected
            await self.audit_repo.create(
                user_id=None,
                action="token_replay_detected",
                ip_address=ip_address,
                user_agent=user_agent,
                payload={"jti": jti}
            )
            raise ValueError("Refresh token has been revoked")

        subject = payload.get("sub")
        if not subject:
            raise ValueError("Invalid token payload")

        user_id = uuid.UUID(subject)
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise ValueError("User inactive or not found")

        # Invalidate old refresh token
        now_ts = datetime.now(timezone.utc).timestamp()
        exp_ts = payload.get("exp", 0)
        ttl = max(1, int(exp_ts - now_ts))
        await self.redis.set(f"blacklist:{jti}", "1", ex=ttl)

        # Generate new pair
        new_token_pair = await self.create_tokens_for_user(user)

        await self.audit_repo.create(
            user_id=user.id,
            action="token_refresh",
            ip_address=ip_address,
            user_agent=user_agent,
            payload={"old_jti": jti}
        )

        return new_token_pair

    async def logout(
        self,
        access_token: str,
        refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Revoke both access and refresh tokens by adding their JTIs to the Redis blacklist."""
        now_ts = datetime.now(timezone.utc).timestamp()
        user_id = None

        # Blacklist Access Token
        try:
            acc_payload = decode_token(access_token, settings.JWT_SECRET_KEY)
            acc_jti = acc_payload.get("jti")
            acc_exp = acc_payload.get("exp", 0)
            acc_sub = acc_payload.get("sub")
            if acc_sub:
                user_id = uuid.UUID(acc_sub)
            if acc_jti:
                ttl = max(1, int(acc_exp - now_ts))
                await self.redis.set(f"blacklist:{acc_jti}", "1", ex=ttl)
        except jwt.PyJWTError:
            pass  # Already invalid or expired

        # Blacklist Refresh Token
        try:
            ref_payload = decode_token(refresh_token, settings.JWT_REFRESH_SECRET_KEY)
            ref_jti = ref_payload.get("jti")
            ref_exp = ref_payload.get("exp", 0)
            if ref_jti:
                ttl = max(1, int(ref_exp - now_ts))
                await self.redis.set(f"blacklist:{ref_jti}", "1", ex=ttl)
        except jwt.PyJWTError:
            pass  # Already invalid or expired

        await self.audit_repo.create(
            user_id=user_id,
            action="user_logout",
            ip_address=ip_address,
            user_agent=user_agent,
            payload={}
        )
