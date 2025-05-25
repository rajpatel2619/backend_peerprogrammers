from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from enum import Enum
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import inspect  # Add this import at the top
from ..database import SessionLocal
from ..models import Course, User, CourseMode, CourseDetails, CourseAuthor

router = APIRouter()

# ─── DB Dependency ───────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ─── ENUM & SCHEMA ───────────────────────────────────────────────
class CourseModeEnum(str, Enum):
    live = "Live"
    offline = "Offline"
    recorded = "Recorded"
    hybrid = "Hybrid"

class CourseCreate(BaseModel):
    title: str
    description: str | None = None
    mode: CourseModeEnum
    creator_ids: list[int]  # Accept multiple creators

# ─── Endpoint: Create Course ─────────────────────────────────────
@router.post("/courses")
def create_course(payload: CourseCreate, db: Session = Depends(get_db)):
    try:
        # ✅ Check if 'courses' table exists
        inspector = inspect(db.get_bind())
        if 'courses' not in inspector.get_table_names():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="The 'courses' table does not exist in the database"
            )
        
        new_course = Course(
            title=payload.title,
            description=payload.description,
            mode=CourseMode[payload.mode.value.lower()],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True
        )
        db.add(new_course)
        # db.refresh(new_course)
        db.flush()  # <-- Flush here to assign new_course.id

        # Create course details with default values
        new_course_details = CourseDetails(
            course_id=new_course.id,  # Generate a unique course_id
            syllabus_summary="Default syllabus summary",
            syllabus_path="default/path",
            venue="Default venue",
            start_date=datetime.utcnow().date(),
            end_date=datetime.utcnow().date(),
            start_time=datetime.utcnow().time(),
            end_time=datetime.utcnow().time(),
            duration_in_hours=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(new_course_details)
        # db.refresh(new_course_details)

      

        # Add course authors
        for creator in payload.creator_ids:
            course_author = CourseAuthor(
                course_id=new_course.id,
                user_id=creator,
                role="Lead",  # You can customize the role as needed
                joined_at=datetime.utcnow()
            )
            db.add(course_author)
            # db.refresh(course_author)  # Refresh to get the latest state of the course
        db.commit()

        return {
            "message": "Course created successfully",
            "course": {
                "id": new_course.id,
                "title": new_course.title,
                "mode": new_course.mode.value,
                "creator_ids": payload.creator_ids,
            }
        }
    except HTTPException:
        raise  # Re-raise HTTPException if it's already one
    except Exception as e:
        # Log the error for debugging purposes
        print(f"An error occurred: {e}")
        db.rollback()  # Rollback in case of error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the course"
        )
