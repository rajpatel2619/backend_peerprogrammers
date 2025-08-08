from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from ..connection.database import Base

class CourseRegistration(Base):
    __tablename__ = "course_registrations"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)

    payment_date = Column(DateTime, nullable=True)
    transaction_id = Column(String(100), nullable=True)

    fee = Column(Float, nullable=True)

    joined_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)\
    
    # Relationships
    user = relationship("User", backref="registrations")
    course = relationship("Courses", backref="registrations")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    registration_id = Column(Integer, ForeignKey("course_registrations.id"), nullable=False)

    amount = Column(Float, nullable=False)  # In rupees or major unit
    currency = Column(String(10), default="INR")
    status = Column(String(30), default="created")  # created, authorized, captured, failed, etc.

    # Razorpay fields
    razorpay_payment_id = Column(String(100), unique=True, nullable=True)
    razorpay_order_id = Column(String(100), nullable=True)
    razorpay_signature = Column(String(255), nullable=True)

    payment_method = Column(String(50), nullable=True)   # card, netbanking, etc.
    email = Column(String(100), nullable=True)
    contact = Column(String(20), nullable=True)

    # Timestamps
    payment_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    registration = relationship("CourseRegistration", backref="payments")