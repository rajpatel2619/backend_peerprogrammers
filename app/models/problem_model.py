from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Enum,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime
from ..connection.database import Base

# ==============================================
# Association Model: ProblemTag
# ==============================================
class ProblemTag(Base):
    __tablename__ = "problem_tags"
    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey("coding_problems.id", ondelete="CASCADE"), nullable=False)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    # Relationships
    problem = relationship("CodingProblem", back_populates="problem_tags")
    tag = relationship("Tag", back_populates="problem_tags")

# ==============================================
# Association Model: ProblemCompany
# ==============================================
class ProblemCompany(Base):
    __tablename__ = "problem_companies"
    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey("coding_problems.id", ondelete="CASCADE"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    # Relationships
    problem = relationship("CodingProblem", back_populates="problem_companies")
    company = relationship("Company", back_populates="problem_companies")



from sqlalchemy import Boolean
# ==============================================
# Tag Model
# ==============================================
class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    added_by = Column(Integer, ForeignKey("users.id"))
    deleted = Column(Boolean, default=False, nullable=False)  # <--- soft delete flag
    # Relationships
    problem_tags = relationship("ProblemTag", back_populates="tag", cascade="all, delete-orphan")
    problems = relationship("CodingProblem", secondary="problem_tags", viewonly=True)

    
# ==============================================
# Company Model
# ==============================================
class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    added_by = Column(Integer, ForeignKey("users.id"))
    deleted = Column(Boolean, default=False, nullable=False)
    # Relationships
    problem_companies = relationship("ProblemCompany", back_populates="company", cascade="all, delete-orphan")
    problems = relationship("CodingProblem", secondary="problem_companies", viewonly=True)
# ==============================================
# Coding Problem Model
# ==============================================
class CodingProblem(Base):
    __tablename__ = "coding_problems"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    link = Column(String(500), unique=True, nullable=False)  # <-- change nullable if needed
    difficulty = Column(Enum("Easy", "Medium", "Hard", name="difficulty_levels"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    gitHubLink = Column(String(500))
    hindiSolution = Column(String(500))
    englishSolution = Column(String(500))
    deleted = Column(Boolean, default=False, nullable=False)

    # ✅ New Column
    is_premium = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="problems")
    sheets = relationship("SheetProblem", back_populates="problem", cascade="all, delete-orphan")
    # Tags
    problem_tags = relationship("ProblemTag", back_populates="problem", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="problem_tags", viewonly=True)
    # Companies
    problem_companies = relationship("ProblemCompany", back_populates="problem", cascade="all, delete-orphan")
    companies = relationship("Company", secondary="problem_companies", viewonly=True)
    # Favorites
    favorites = relationship("Favorite", back_populates="problem", cascade="all, delete-orphan")


# ==============================================
# Sheet Model
# ==============================================
class Sheet(Base):
    __tablename__ = "sheets"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    deleted = Column(Boolean, default=False, nullable=False)
    # Relationships
    problems = relationship("SheetProblem", back_populates="sheet", cascade="all, delete-orphan")

# ==============================================
# SheetProblem Mapping Model
# ==============================================
class SheetProblem(Base):
    __tablename__ = "sheet_problems"
    id = Column(Integer, primary_key=True)
    sheet_id = Column(Integer, ForeignKey("sheets.id", ondelete="CASCADE"))
    problem_id = Column(Integer, ForeignKey("coding_problems.id", ondelete="CASCADE"))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    deleted = Column(Boolean, default=False, nullable=False)
    # Relationships
    sheet = relationship("Sheet", back_populates="problems")
    problem = relationship("CodingProblem", back_populates="sheets")

# ==============================================
# Favorite Model
# ==============================================
class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    problem_id = Column(Integer, ForeignKey("coding_problems.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    deleted = Column(Boolean, default=False, nullable=False)
    # Relationships
    user = relationship("User", back_populates="favorites")
    problem = relationship("CodingProblem", back_populates="favorites")
