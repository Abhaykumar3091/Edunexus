from typing import AsyncGenerator, Callable, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole

# OAuth2 scheme configured to use the auth login endpoint
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False,
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validate the incoming JWT token, decode the claims, and fetch
    the active User from the database using asyncpg.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception

    try:
        # Search by id (numeric) or email
        if str(user_id).isdigit():
            query = select(User).where(User.id == int(user_id))
        else:
            query = select(User).where(User.email == str(user_id))
        
        result = await db.execute(query)
        user = result.scalar_one_or_none()
    except Exception:
        raise credentials_exception

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )

    return user


def require_roles(allowed_roles: List[UserRole]) -> Callable:
    """
    Enforces Role-Based Access Control (RBAC).
    Validates that the authenticated user belongs to one of the allowed roles.
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required role: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return role_checker


# Role-specific dependency shortcuts
get_current_student = require_roles([UserRole.STUDENT])
get_current_faculty = require_roles([UserRole.FACULTY])
get_current_admin = require_roles([UserRole.ADMIN])
get_faculty_or_admin = require_roles([UserRole.FACULTY, UserRole.ADMIN])
