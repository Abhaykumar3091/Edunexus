"""
Admin API Endpoints — Platform statistics, user management, knowledge documents.
All endpoints require ADMIN role.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.response import StandardResponse
from app.schemas.student import AdminStatsSchema
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("/stats", response_model=StandardResponse[AdminStatsSchema], tags=["Admin"])
async def get_platform_stats(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get platform-wide statistics: user counts and summary.
    """
    total_students = (await db.execute(
        select(func.count(User.id)).where(User.role == UserRole.STUDENT)
    )).scalar_one()
    total_faculty = (await db.execute(
        select(func.count(User.id)).where(User.role == UserRole.FACULTY)
    )).scalar_one()
    total_admins = (await db.execute(
        select(func.count(User.id)).where(User.role == UserRole.ADMIN)
    )).scalar_one()

    return StandardResponse(
        success=True,
        data=AdminStatsSchema(
            total_students=total_students,
            total_faculty=total_faculty,
            total_admins=total_admins,
            total_users=total_students + total_faculty + total_admins,
            open_complaints=0,
            resolved_complaints=0,
            total_complaints=0,
        ),
        message="Platform statistics retrieved successfully.",
    )


@router.get("/users", response_model=StandardResponse[List[UserResponse]], tags=["Admin"])
async def list_users(
    role: Optional[str] = None,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    List all platform users. Optionally filter by role (STUDENT / FACULTY / ADMIN).
    """
    stmt = select(User).order_by(User.created_at.desc())
    if role:
        try:
            role_enum = UserRole(role.upper())
            stmt = stmt.where(User.role == role_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role filter '{role}'. Must be STUDENT, FACULTY, or ADMIN.",
            )

    result = await db.execute(stmt)
    users = result.scalars().all()

    return StandardResponse(
        success=True,
        data=[UserResponse.model_validate(u) for u in users],
        message=f"{len(users)} user(s) retrieved.",
    )


@router.get("/documents", response_model=StandardResponse[List[dict]], tags=["Admin"])
async def list_knowledge_documents(
    _: User = Depends(get_current_admin),
):
    """
    List all documents stored in Azure Blob Storage (university knowledge base).
    """
    from app.services.azure_storage import list_documents
    docs = await list_documents()
    return StandardResponse(
        success=True,
        data=docs,
        message=f"{len(docs)} document(s) found in knowledge base.",
    )
