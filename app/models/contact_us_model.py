from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from ..connection.database import Base  # Ensure this is your SQLAlchemy Base instance

class ContactUs(Base):
    __tablename__ = "contact_us"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    inquiry_type = Column(String(50), default="general")  # matches "type" from frontend
    subject = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ContactUs(name='{self.name}', email='{self.email}', subject='{self.subject}')>"
