import logging
from datetime import datetime
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.student_data import (
    Student,
    Complaint,
    ComplaintCategory,
    ComplaintStatus,
)

logger = logging.getLogger(__name__)


async def seed_student_demo_data() -> None:
    """Seed sample student profile and complaints."""
    async with AsyncSessionLocal() as session:
        # Find student user
        res = await session.execute(
            select(User).where(User.email == "student@university.edu")
        )
        student_user = res.scalar_one_or_none()
        if not student_user:
            return

        # Check if student profile already exists
        stu_prof_res = await session.execute(
            select(Student).where(Student.user_id == student_user.id)
        )
        student = stu_prof_res.scalar_one_or_none()
        if not student:
            student = Student(
                user_id=student_user.id,
                program="B.Tech Computer Science and Engineering",
                semester=6,
                section="A",
                batch_year=2023,
                cgpa=8.75,
            )
            session.add(student)
            await session.flush()

            # Add sample complaints
            c1 = Complaint(
                student_id=student.id,
                ticket_id="TKT-2026-001",
                category=ComplaintCategory.HOSTEL,
                title="Hostel Block B Room 304 AC not cooling",
                description="The AC in room 304 has not been functioning properly for the past 3 days.",
                status=ComplaintStatus.IN_REVIEW,
                assigned_to="Hostel Warden Office",
            )
            c2 = Complaint(
                student_id=student.id,
                ticket_id="TKT-2026-002",
                category=ComplaintCategory.ACADEMIC,
                title="Elective course registration portal issue",
                description="Encountered network timeout when attempting to register for Distributed Systems.",
                status=ComplaintStatus.RESOLVED,
                assigned_to="Academic Registrar",
                resolution_notes="Student manually enrolled.",
                resolved_at=datetime.utcnow(),
            )
            session.add_all([c1, c2])
            await session.commit()
            logger.info("Demo student profile and complaints seeded successfully.")
