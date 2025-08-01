from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from ..connection.database import Base

class CourseRegistration(Base):
    __tablename__ = "course_registrations"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)

    is_verified = Column(Boolean, default=False)
    has_paid = Column(Boolean, default=False)
    payment_mode = Column(String(50), nullable=True)
    payment_date = Column(DateTime, nullable=True)
    transaction_id = Column(String(100), nullable=True)

    fee = Column(Float, nullable=True)
    discount_amount = Column(Float, default=0.0)
    final_fee = Column(Float, nullable=True)
    coupon_code = Column(String(50), nullable=True)

    joined_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed = Column(DateTime, nullable=True)

    feedback = Column(Text, nullable=True)
    progress = Column(Integer, default=0)
    certificate_issued = Column(Boolean, default=False)
    completion_date = Column(DateTime, nullable=True)

    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", backref="registrations")
    course = relationship("Courses", backref="registrations")
