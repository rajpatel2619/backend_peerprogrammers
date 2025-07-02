from sqlalchemy import (
    Column, Integer, String, Boolean, Date, DateTime, Time, Enum, ForeignKey, Table
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from ..connection.database import Base
from ..schemas.course_schema import CourseMode





# class Course(Base):
#     __tablename__ = "courses_1"

#     id = Column(Integer, primary_key=True, index=True)
#     creatorid = Column(Integer, ForeignKey("users.id"), nullable=False)
#     title = Column(String(255), nullable=False)
#     category = Column(String(100), nullable=False)
#     type = Column(Enum(CourseMode), nullable=False, default=CourseMode.live)
#     is_published = Column(Boolean, default=False)
    
#     created_at = Column(DateTime, default=datetime.utcnow)
#     updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

   
#     details = relationship("CourseDetails", back_populates="course", uselist=False)



# class CourseDetails(Base):
#     __tablename__ = "course_details_1"

#     id = Column(Integer, primary_key=True, index=True)
#     course_id = Column(Integer, ForeignKey("courses_1.id"), nullable=False)

#     syllabus_link = Column(String(255), nullable=True)
#     co_mentors = Column(String(255), nullable=True)

#     created_at = Column(DateTime, default=datetime.utcnow)
#     updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

#     # Optional: Add relationship if needed
#     course = relationship("Course", back_populates="details", lazy="joined")


# class CourseAuthor(Base):
#     __tablename__ = "course_authors"

#     course_id = Column(Integer, ForeignKey("courses.id"), primary_key=True)
#     user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
#     role = Column(String(255))  # e.g., "Lead", "Co-Instructor"
#     joined_at = Column(DateTime, default=datetime.utcnow)



class IndividualCourse(Base):
    __tablename__ = "individual_course"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(255), nullable=False)
    mode = Column(String(50), nullable=False)
    creatorid = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_published = Column(Boolean, default=False)

    syllabus_link = Column(String(255), nullable=True)
    co_mentors = Column(String(255), nullable=True)
    cover_photo = Column(String(255), nullable=True)
    description = Column(String(1000), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    daily_meeting_link = Column(String(255), nullable=True)

    price = Column(Integer, nullable = True)
    lecture_link = Column(String(255), nullable=True)

    domains = Column(String(1000), nullable=True)

    # Basic Plan Fields
    basic_seats = Column(String(10), nullable=True)
    basic_price = Column(String(20), nullable=True)
    basic_whatsapp = Column(String(255), nullable=True)
    basic_meeting_link = Column(String(255), nullable=True)

    # Premium Plan Fields
    premium_seats = Column(String(10), nullable=True)
    premium_price = Column(String(20), nullable=True)
    premium_whatsapp = Column(String(255), nullable=True)
    premium_meeting_link = Column(String(255), nullable=True)

    # Ultra Plan Fields
    ultra_seats = Column(String(10), nullable=True)
    ultra_price = Column(String(20), nullable=True)
    ultra_whatsapp = Column(String(255), nullable=True)
    ultra_meeting_link = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    mentors = relationship("CourseMentor", back_populates="course", cascade="all, delete-orphan")
    domain_tags = relationship("CourseDomain", back_populates="course", cascade="all, delete-orphan")


class CourseMentor(Base):
    __tablename__ = "course_mentors"

    course_id = Column(Integer, ForeignKey("individual_course.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    role = Column(String(255))  # e.g., "Lead", "Assistant"
    joined_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("IndividualCourse", back_populates="mentors")


class CourseDomain(Base):
    __tablename__ = "course_domains"

    course_id = Column(Integer, ForeignKey("individual_course.id"), primary_key=True)
    domain = Column(String(100), primary_key=True)

    course = relationship("IndividualCourse", back_populates="domain_tags")
