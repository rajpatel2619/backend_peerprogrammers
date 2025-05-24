from sqlalchemy import (
    Column, Integer, String, Boolean, Date, DateTime, Time, Enum, ForeignKey, Table
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

# Enum for course mode
class CourseMode(enum.Enum):
    live = "Live"
    offline = "Offline"
    recorded = "Recorded"
    hybrid = "Hybrid"


# Association table for many-to-many relationship between Course and User (creators)
course_creators = Table(
    'course_creators',
    Base.metadata,
    Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True),
    Column('creator_id', Integer, ForeignKey('users.id'), primary_key=True)
)

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    description = Column(String(255))


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    active = Column(Boolean, default=True)

    # Relationship to courses (many-to-many)
    # courses = relationship("Course", secondary=course_creators, back_populates="creators")


class UserDetails(Base):
    __tablename__ = "userDetails"

    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey("users.id"), nullable=False)
    firstName = Column(String(100))
    lastName = Column(String(100))
    phoneNumber = Column(String(20))
    email = Column(String(255))
    address = Column(String(255))
    dob = Column(Date)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserSocialDetails(Base):
    __tablename__ = "userSocialDetails"

    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey("users.id"), nullable=False)
    facebook = Column(String(255))
    github = Column(String(255))
    linkedin = Column(String(255))
    medium = Column(String(255))
    youtube = Column(String(255))
    twitter = Column(String(255))
    instagram = Column(String(255))
    personalWebsite = Column(String(255))
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CourseDetails(Base):
    __tablename__ = "course_details"

    id = Column(Integer, primary_key=True, index=True)  # Internal DB ID
    course_id = Column(String, unique=True, nullable=False, index=True)  # Public-facing course identifier

    syllabus_summary = Column(String, nullable=True)  # Short text overview
    syllabus_path = Column(String, nullable=True)     # Path or URL to full syllabus file/link

    venue = Column(String, nullable=True)

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
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
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
    role = Column(String)  # e.g., "Lead", "Co-Instructor"
    joined_at = Column(DateTime, default=datetime.utcnow)
