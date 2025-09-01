from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from datetime import datetime
from ..connection.database import Base

# ==============================================
# Organization Model
# ==============================================
class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    poc_name = Column(String(255), nullable=False)  # Point of Contact name
    poc_contact_number = Column(String(20), nullable=False)
    poc_email = Column(String(255), nullable=False)
    address = Column(Text, nullable=False)
    message = Column(Text, nullable=True)
    expected_participants = Column(Integer, nullable=True)  # New field
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted = Column(Boolean, default=False, nullable=False)
