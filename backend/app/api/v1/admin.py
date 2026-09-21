"""
Admin API Endpoints — Platform statistics, user management, complaint management.
All endpoints require ADMIN role.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.student_data import Complaint, ComplaintStatus
from app.schemas.response import StandardResponse
from app.schemas.student import AdminStatsSchema, ComplaintSchema, ComplaintStatusUpdate
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("/stats", response_model=StandardResponse[AdminStatsSchema], tags=["Admin"])
async def get_platform_stats(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get platform-wide statistics: user counts, complaint summary.
    """
    # User counts by role
    total_students = (await db.execute(
        select(func.count(User.id)).where(User.role == UserRole.STUDENT)
    )).scalar_one()
    total_faculty = (await db.execute(
        select(func.count(User.id)).where(User.role == UserRole.FACULTY)
    )).scalar_one()
    total_admins = (await db.execute(
        select(func.count(User.id)).where(User.role == UserRole.ADMIN)
    )).scalar_one()

    # Complaint counts
    open_complaints = (await db.execute(
        select(func.count(Complaint.id)).where(
            Complaint.status.in_([ComplaintStatus.OPEN, ComplaintStatus.ASSIGNED, ComplaintStatus.IN_PROGRESS])
        )
    )).scalar_one()
    resolved_complaints = (await db.execute(
        select(func.count(Complaint.id)).where(
            Complaint.status.in_([ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED])
        )
    )).scalar_one()
    total_complaints = (await db.execute(
        select(func.count(Complaint.id))
    )).scalar_one()

    return StandardResponse(
        success=True,
        data=AdminStatsSchema(
            total_students=total_students,
            total_faculty=total_faculty,
            total_admins=total_admins,
            total_users=total_students + total_faculty + total_admins,
            open_complaints=open_complaints,
            resolved_complaints=resolved_complaints,
            total_complaints=total_complaints,
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


@router.get("/complaints", response_model=StandardResponse[List[ComplaintSchema]], tags=["Admin"])
async def list_all_complaints(
    complaint_status: Optional[str] = None,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    List all complaints across all students. Optionally filter by status.
    """
    stmt = select(Complaint).order_by(Complaint.created_at.desc())
    if complaint_status:
        try:
            status_enum = ComplaintStatus(complaint_status.upper())
            stmt = stmt.where(Complaint.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status '{complaint_status}'.",
            )

    result = await db.execute(stmt)
    complaints = result.scalars().all()

    return StandardResponse(
        success=True,
        data=[ComplaintSchema.model_validate(c) for c in complaints],
        message=f"{len(complaints)} complaint(s) retrieved.",
    )


@router.patch("/complaints/{complaint_id}", response_model=StandardResponse[ComplaintSchema], tags=["Admin"])
async def update_complaint_status(
    complaint_id: int,
    update: ComplaintStatusUpdate,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update the status and resolution notes of a complaint ticket.
    """
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    complaint = result.scalar_one_or_none()

    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint with ID {complaint_id} not found.",
        )

    try:
        complaint.status = ComplaintStatus(update.status.upper())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status value '{update.status}'.",
        )

    if update.assigned_to is not None:
        complaint.assigned_to = update.assigned_to
    if update.resolution_notes is not None:
        complaint.resolution_notes = update.resolution_notes

    await db.commit()
    await db.refresh(complaint)

    return StandardResponse(
        success=True,
        data=ComplaintSchema.model_validate(complaint),
        message="Complaint status updated successfully.",
    )


@router.get("/documents", response_model=StandardResponse[List[dict]], tags=["Admin"])
async def list_knowledge_documents(
    _: User = Depends(get_current_admin),
):
    """
    List all documents stored in Azure Blob Storage (university knowledge base).
    Falls back to mock document list if Blob Storage is not configured.
    """
    from app.services.azure_storage import list_documents
    docs = await list_documents()
    return StandardResponse(
        success=True,
        data=docs,
        message=f"{len(docs)} document(s) found in knowledge base.",
    )
