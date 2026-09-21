import enum
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class ComplaintCategory(str, enum.Enum):
    HOSTEL = "HOSTEL"
    ACADEMIC = "ACADEMIC"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    ADMINISTRATIVE = "ADMINISTRATIVE"
    OTHER = "OTHER"


class ComplaintStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    IN_REVIEW = "IN_REVIEW"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    program = Column(String(100), nullable=False)
    semester = Column(Integer, nullable=False)
    section = Column(String(10), nullable=False)
    batch_year = Column(Integer, nullable=False)
    cgpa = Column(Float, nullable=True)

    # Relationships
    user = relationship("User")
    complaints = relationship("Complaint", back_populates="student")


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    ticket_id = Column(String(50), unique=True, index=True, nullable=False)
    category = Column(Enum(ComplaintCategory), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum(ComplaintStatus), default=ComplaintStatus.SUBMITTED)
    assigned_to = Column(String(100), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    student = relationship("Student", back_populates="complaints")


class DocumentReference(Base):
    __tablename__ = "document_references"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    blob_url = Column(String(500), nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    metadata_json = Column(JSON, nullable=True)
