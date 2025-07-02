from sqlalchemy import (
    Column, Integer, String, Boolean, Date, DateTime, Time, Enum, ForeignKey, Table
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from ..connection.database import Base  # Assuming you have a database.py file with Base defined

from ..schemas.course_schema import *

# Enum for course mode



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
    # isStudent = Column(Boolean, default=True)


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


