from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User, UserRole
from app.schemas.response import StandardResponse
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserLogin, UserResponse

router = APIRouter()


@router.post("/register", response_model=StandardResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user account with Argon2id password hashing.
    """
    # Check for existing email
    query = select(User).where(User.email == user_in.email.lower())
    existing = await db.execute(query)
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    # Check for existing university_id if provided
    if user_in.university_id:
        u_query = select(User).where(User.university_id == user_in.university_id)
        existing_u = await db.execute(u_query)
        if existing_u.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this University ID already exists.",
            )

    # Create new user with Argon2id hash
    new_user = User(
        email=user_in.email.lower(),
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
        phone_number=user_in.phone_number,
        university_id=user_in.university_id,
        is_active=True,
        is_verified=False,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return StandardResponse(
        success=True,
        data=UserResponse.model_validate(new_user),
        message="User account registered successfully.",
    )


@router.post("/login", response_model=StandardResponse[Token])
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user with email and password via Argon2id.
    Returns signed JWT access token.
    """
    query = select(User).where(User.email == login_data.email.lower())
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive. Please contact administration.",
        )

    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        subject=user.id,
        role=user.role.value,
        extra_claims={"email": user.email, "name": user.full_name},
        expires_delta=expires_delta,
    )

    token_data = Token(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        role=user.role.value,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
    )

    return StandardResponse(
        success=True,
        data=token_data,
        message="Login successful.",
    )


@router.post("/token", response_model=Token, include_in_schema=False)
async def login_oauth2_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    OAuth2 standard compatible token endpoint for Swagger UI authorization.
    """
    query = select(User).where(User.email == form_data.username.lower())
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        subject=user.id,
        role=user.role.value,
        extra_claims={"email": user.email, "name": user.full_name},
    )

    return Token(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        role=user.role.value,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
    )


@router.get("/me", response_model=StandardResponse[UserResponse])
async def read_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve authenticated user's profile and RBAC role.
    """
    return StandardResponse(
        success=True,
        data=UserResponse.model_validate(current_user),
        message="Current user profile retrieved.",
    )
