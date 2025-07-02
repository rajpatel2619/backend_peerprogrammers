# app/models/book_model.py

from sqlalchemy import Column, Integer, String
from app.connection.database import Base  # import the shared Base

class Testing(Base):
    __tablename__ = "Atuomatically Created"

    id = Column(Integer, primary_key=True, index=True)
