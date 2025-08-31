from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime
from sqlalchemy.orm import relationship
from ..connection.database import Base

class CustomerPayment(Base):
    __tablename__ = "new_registrations"

    id = Column(Integer, primary_key=True, index=True)

    # User details
    name = Column(String(100), nullable=False)
    number = Column(String(20), nullable=False)
    email = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)

    # Course relationship
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)

    # Payment details
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")
    status = Column(String(30), default="created")  # created, authorized, captured, failed, etc.

    razorpay_payment_id = Column(String(100), unique=True, nullable=True)
    razorpay_order_id = Column(String(100), nullable=True)
    razorpay_signature = Column(String(255), nullable=True)

    payment_method = Column(String(50), nullable=True)

    # Timestamps
    payment_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with courses
    course = relationship("Courses", backref="customer_payments")
