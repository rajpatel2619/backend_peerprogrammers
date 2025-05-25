from sqlalchemy import (
    Column, Integer, String, Boolean, Date, DateTime, Time, Enum, ForeignKey, Table
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from ..connection.database import Base
from ..schemas.course_schema import CourseMode




class CourseDetails(Base):
    __tablename__ = "course_details"

    id = Column(Integer, primary_key=True, index=True)  # Internal DB ID
    course_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    syllabus_summary = Column(String(255), nullable=True)  # Short text overview
    syllabus_path = Column(String(255), nullable=True)     # Path or URL to full syllabus file/link

    venue = Column(String(255), nullable=True)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)

    duration_in_hours = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    mode = Column(Enum(CourseMode), nullable=False, default=CourseMode.live)  # Live / Offline / Recorded / Hybrid

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to users through the association table
    # creators = relationship("User", secondary=course_creators, back_populates="courses")


class CourseAuthor(Base):
    __tablename__ = "course_authors"

    course_id = Column(Integer, ForeignKey("courses.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    role = Column(String(255))  # e.g., "Lead", "Co-Instructor"
    joined_at = Column(DateTime, default=datetime.utcnow)
