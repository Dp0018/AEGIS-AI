import uuid
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.user import UserCreate

class UserRepository:
    """Repository class managing user database query/mutation operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Fetch a single user by their primary key UUID."""
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Fetch a single user by their unique email identifier."""
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, user_in: UserCreate, hashed_password: str) -> User:
        """Persist a new user entity in the database."""
        user = User(
            email=user_in.email,
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            role=user_in.role,
            is_active=True
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def count(self) -> int:
        """Count the total number of users registered in the database."""
        query = select(func.count()).select_from(User)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def list_all(self) -> list[User]:
        """Fetch all registered platform users sorted by created_at."""
        query = select(User).order_by(User.created_at.asc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
