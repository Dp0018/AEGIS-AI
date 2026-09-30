import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import get_db_session
from app.db.redis import get_redis
import redis.asyncio as aioredis
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import Token, TokenRefreshRequest
from app.schemas.common import ErrorResponse
from app.core.dependencies import get_auth_service, get_current_user, get_user_repository
from app.services.auth import AuthService

router = APIRouter()

# Optional OAuth2 Password Bearer to allow admin bootstrapping
oauth2_scheme_opt = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_PREFIX}/auth/token",
    auto_error=False
)

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse}
    }
)
async def register(
    user_in: UserCreate,
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme_opt),
    db: AsyncSession = Depends(get_db_session),
    user_repo: UserRepository = Depends(get_user_repository),
    redis: aioredis.Redis = Depends(get_redis),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new operator or admin user.
    
    If no users exist in the system, the first user is bootstrapped as ADMIN.
    Subsequent registrations require an active ADMIN session.
    """
    user_count = await user_repo.count()
    if user_count > 0:
        # Require active Admin authentication
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required for registration"
            )
        try:
            payload = decode_token(token, settings.JWT_SECRET_KEY)
            subject = payload.get("sub")
            jti = payload.get("jti")
            if not subject or not jti:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials"
                )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
            
        # Check blacklist
        is_blacklisted = await redis.exists(f"blacklist:{jti}")
        if is_blacklisted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or logged out"
            )

        caller = await user_repo.get_by_id(uuid.UUID(subject))
        if not caller or not caller.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        if caller.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can register new users"
            )

    try:
        ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        user = await auth_service.register_user(user_in, ip_address=ip, user_agent=user_agent)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post(
    "/token",
    response_model=Token,
    responses={400: {"model": ErrorResponse}}
)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Authenticate user credentials using standard OAuth2 Password Form data."""
    try:
        ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        user = await auth_service.authenticate_user(
            email=form_data.username,
            plain_password=form_data.password,
            ip_address=ip,
            user_agent=user_agent
        )
        tokens = await auth_service.create_tokens_for_user(user)
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post(
    "/refresh",
    response_model=Token,
    responses={400: {"model": ErrorResponse}}
)
async def refresh_token(
    request: Request,
    refresh_in: TokenRefreshRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Perform Refresh Token Rotation to retrieve a new pair of credentials."""
    try:
        ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        tokens = await auth_service.refresh_access_token(
            refresh_token=refresh_in.refresh_token,
            ip_address=ip,
            user_agent=user_agent
        )
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    responses={401: {"model": ErrorResponse}}
)
async def logout(
    request: Request,
    logout_in: TokenRefreshRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Revoke both access and refresh tokens for the current session."""
    # Retrieve access token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
        
    access_token = auth_header.split(" ")[1]
    ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    await auth_service.logout(
        access_token=access_token,
        refresh_token=logout_in.refresh_token,
        ip_address=ip,
        user_agent=user_agent
    )
    return {"detail": "Successfully logged out"}

# Test routes to verify RBAC security layers
from app.core.dependencies import get_admin_user, get_operator_user

@router.get("/test-admin")
async def test_admin_endpoint(current_user: User = Depends(get_admin_user)):
    """Test endpoint accessible only by administrators."""
    return {"message": "Welcome Admin", "email": current_user.email}

@router.get("/test-operator")
async def test_operator_endpoint(current_user: User = Depends(get_operator_user)):
    """Test endpoint accessible by operators and administrators."""
    return {"message": "Welcome Operator", "email": current_user.email}

@router.get(
    "/users",
    response_model=List[UserResponse],
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse}
    }
)
async def list_users(
    current_user: User = Depends(get_admin_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """List all registered platform user profiles. Restricted to administrators."""
    users = await user_repo.list_all()
    return users

