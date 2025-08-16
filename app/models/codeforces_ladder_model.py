from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime, Boolean, Text
)
from sqlalchemy.orm import relationship
from datetime import datetime
from ..connection.database import Base



class CP51Problem(Base):
    __tablename__ = "cp51_problem"

    id = Column(Integer, primary_key=True, index=True)

    # Core problem details
    title = Column(String(255), nullable=False)  # Title of Problem
    problem_link = Column(String(500), nullable=False)  # Link to online judge problem
    
    # Difficulty can be string or rating number
    difficulty = Column(String(50), nullable=True)  # Easy, Medium, Hard
    rating = Column(Integer, nullable=True)  # Optional e.g. 800,1200,1600

    # Solutions
    description = Column(Text, nullable=True)
    github_solution_link = Column(String(500), nullable=True)
    hindi_solution_link = Column(String(500), nullable=True)
    english_solution_link = Column(String(500), nullable=True)

    # Metadata
    created_by = Column(
        Integer, 
        ForeignKey("users.id", ondelete="SET NULL"), 
        nullable=True
    )
    is_premium = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    creator = relationship("User", back_populates="problem_resources")


# ==============================================
# Ladder Table
# ==============================================
class Ladder(Base):
    __tablename__ = "ladders"

    id = Column(Integer, primary_key=True)
    rating_range = Column(String(255), nullable=False)
    url = Column(String(500), unique=True, nullable=False)
    lower_bound = Column(Integer, nullable=True)
    upper_bound = Column(Integer, nullable=True)
    problem_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    problems = relationship(
        "LadderProblem",
        back_populates="ladder",
        cascade="all, delete-orphan"
    )


# ==============================================
# Ladder Problem Solution Table
# ==============================================
class LadderProblemSolution(Base):
    __tablename__ = "ladder_problem_solutions"

    id = Column(Integer, primary_key=True)
    problem_id = Column(
        Integer,
        ForeignKey("ladder_problems.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    platform = Column(String(50), nullable=False)
    link = Column(String(500), nullable=False)

    # Relationships
    problem = relationship("LadderProblem", back_populates="solutions")


# ==============================================
# Ladder Problem Table
# ==============================================
class LadderProblem(Base):
    __tablename__ = "ladder_problems"

    id = Column(Integer, primary_key=True)
    ladder_id = Column(
        Integer,
        ForeignKey("ladders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    problem_order = Column(Integer, nullable=True)
    problem_name = Column(String(255), nullable=False)
    problem_url = Column(String(500), nullable=False)
    online_judge = Column(String(50), nullable=True)
    difficulty = Column(String(20), nullable=True)

    # Relationships
    ladder = relationship("Ladder", back_populates="problems")
    user_status = relationship(
        "UserProblemStatus",
        back_populates="problem",
        cascade="all, delete-orphan"
    )
    solutions = relationship(
        "LadderProblemSolution",
        back_populates="problem",
        cascade="all, delete-orphan"
    )

    


# ==============================================
# User Problem Status Table
# ==============================================
class UserProblemStatus(Base):
    __tablename__ = "user_problem_status"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    problem_id = Column(
        Integer,
        ForeignKey("ladder_problems.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    is_completed = Column(Boolean, default=False)
    is_revisit = Column(Boolean, default=False)
    checked_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    problem = relationship("LadderProblem", back_populates="user_status")
    user = relationship("User", back_populates="problem_status")




class UserCPProfile(Base):
    __tablename__ = "user_cp_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True  # 1-to-1 relationship
    )

    # Competitive programming info
    codeforces_handle = Column(String(20), nullable=True, index=True)
    codeforces_rating = Column(Integer, nullable=True)
    atcoder_handle = Column(String(20), nullable=True)
    leetcode_handle = Column(String(20), nullable=True)

    last_synced_at = Column(DateTime, default=datetime.utcnow)

    # Relationship back to User
    user = relationship("User", back_populates="cp_profile")


class PendingVerification(Base):
    __tablename__ = "pending_verifications"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    username = Column(String(50), nullable=False)

    problem_id = Column(String(100), nullable=False, index=True)  # Now plain string

    expiry_at = Column(DateTime, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="pending_verifications")
