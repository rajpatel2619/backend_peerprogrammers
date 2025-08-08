from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Enum,
    DateTime,
    ForeignKey,
    Table,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from ..connection.database import Base

# Association Table for CodingProblem <-> Tag (Many-to-Many)
problem_tags = Table(
    "problem_tags",
    Base.metadata,
    Column("problem_id", Integer, ForeignKey("coding_problems.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
)

# -----------------------------
# Tag Model
# -----------------------------
class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

    problems = relationship("CodingProblem", secondary=problem_tags, back_populates="tags")


# -----------------------------
# Coding Problem Model
# -----------------------------
class CodingProblem(Base):
    __tablename__ = "coding_problems"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    link = Column(String(500), unique=True, nullable=False)
    platform = Column(String(100), nullable=False)  # e.g., LeetCode, Codeforces
    difficulty = Column(Enum("Easy", "Medium", "Hard", name="difficulty_levels"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    added_by = Column(Integer, ForeignKey("users.id"))
    solutions = Column(String(1000))

    # Relationships
    user = relationship("User", back_populates="problems")  # Assumes User model has: problems = relationship(...)
    sheets = relationship("SheetProblem", back_populates="problem", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=problem_tags, back_populates="problems")


# -----------------------------
# Sheet Model
# -----------------------------
class Sheet(Base):
    __tablename__ = "sheets"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))  # Optional user link
    created_at = Column(DateTime, default=datetime.utcnow)

    problems = relationship("SheetProblem", back_populates="sheet", cascade="all, delete-orphan")


# -----------------------------
# SheetProblem Mapping Model
# -----------------------------
class SheetProblem(Base):
    __tablename__ = "sheet_problems"

    id = Column(Integer, primary_key=True)
    sheet_id = Column(Integer, ForeignKey("sheets.id", ondelete="CASCADE"))
    problem_id = Column(Integer, ForeignKey("coding_problems.id", ondelete="CASCADE"))

    order = Column(Integer)  # Position/order in the sheet
    note = Column(Text)      # Optional notes like "tricky", "must do", etc.

    sheet = relationship("Sheet", back_populates="problems")
    problem = relationship("CodingProblem", back_populates="sheets")
