from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.student_data import (
    Student,
    Complaint,
    ComplaintStatus,
)
from app.schemas.student import (
    StudentProfileResponse,
    ComplaintCreate,
    ComplaintSchema,
)
from app.schemas.response import StandardResponse

router = APIRouter()


@router.get("/profile", response_model=StandardResponse[StudentProfileResponse])
def get_student_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    profile_data = StudentProfileResponse(
        id=student.id,
        user_id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        university_id=current_user.university_id,
        program=student.program,
        semester=student.semester,
        section=student.section,
        batch_year=student.batch_year,
        cgpa=student.cgpa
    )
    return StandardResponse(success=True, data=profile_data)


@router.get("/complaints", response_model=StandardResponse[List[ComplaintSchema]])
def get_complaints(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    complaints = db.query(Complaint).filter(Complaint.student_id == student.id).all()
    return StandardResponse(success=True, data=complaints)


@router.post("/complaints", response_model=StandardResponse[ComplaintSchema])
def create_complaint(
    complaint_in: ComplaintCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    new_complaint = Complaint(
        student_id=student.id,
        ticket_id=ticket_id,
        category=complaint_in.category,
        title=complaint_in.title,
        description=complaint_in.description,
        status=ComplaintStatus.SUBMITTED
    )
    db.add(new_complaint)
    db.commit()
    db.refresh(new_complaint)
    return StandardResponse(success=True, data=new_complaint, message="Complaint registered successfully")
