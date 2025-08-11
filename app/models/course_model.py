from sqlalchemy import (
    Column, Integer, String, Boolean, Date, DateTime, Time, Enum, ForeignKey, Table
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from ..connection.database import Base
from ..schemas.course_schema import CourseMode



class Courses(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(255), nullable=False)
    mode = Column(String(50), nullable=False)
    creatorid = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_published = Column(Boolean, default=False)

    syllabus_link = Column(String(255), nullable=True)
    syllausContent = Column(String(10000))
    
    co_mentors = Column(String(255), nullable=True)
    
    cover_photo = Column(String(255), nullable=True)
    description = Column(String(1000), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    price = Column(Integer, nullable = True)
    lecture_link = Column(String(255), nullable=True)

    domains = Column(String(1000), nullable=True)
    
    
    seats = Column(Integer, nullable = False)
    chatLink = Column(String(200), nullable = False)
    
    # Extra
    isExtraRegistration = Column(Boolean, default=False)
    isVerified = Column(Boolean, default = False)
    


    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    mentors = relationship("CourseMentor", back_populates="course", cascade="all, delete-orphan")
    domain_tags = relationship("CourseDomain", back_populates="course", cascade="all, delete-orphan")


    creator = relationship("User", back_populates="created_courses")


class CourseMentor(Base):
    __tablename__ = "course_mentors"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(255))
    joined_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Courses", back_populates="mentors")
    user = relationship("User", back_populates="mentorships")



class CourseDomain(Base):
    __tablename__ = "course_domains"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    domain_id = Column(Integer, ForeignKey("domain_tags.id"), nullable=False)

    course = relationship("Courses", back_populates="domain_tags")
    domain = relationship("DomainTag")



class DomainTag(Base):
    __tablename__ = "domain_tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    createdBy = Column(Integer, ForeignKey("users.id"), nullable=False)

    isVerified = Column(Boolean, default=False)

    created_user = relationship("User", foreign_keys=[createdBy], backref="created_domains")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
