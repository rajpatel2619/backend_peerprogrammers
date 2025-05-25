from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import inspect  
from datetime import  datetime
from ...connection.utility import get_db
from ...schemas.course_schema import *
from ...models.course_model import Course, CourseDetails, CourseAuthor
router = APIRouter()

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


# ─── Endpoint: Update Course Details ─────────────────────────────────────
@router.put("/courses/{course_id}/details")
def update_course_details(course_id: int, payload: CourseDetailsUpdate, db: Session = Depends(get_db)):
    try:
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )

        course_details = db.query(CourseDetails).filter(CourseDetails.course_id == course_id).first()
        if not course_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course details not found"
            )

        if payload.syllabus_summary is not None:
            course_details.syllabus_summary = payload.syllabus_summary
        if payload.syllabus_path is not None:
            course_details.syllabus_path = payload.syllabus_path
        if payload.venue is not None:
            course_details.venue = payload.venue
        if payload.start_date is not None:
            course_details.start_date = payload.start_date
        if payload.end_date is not None:
            course_details.end_date = payload.end_date
        if payload.start_time is not None:
            course_details.start_time = payload.start_time
        if payload.end_time is not None:
            course_details.end_time = payload.end_time
        if payload.duration_in_hours is not None:
            course_details.duration_in_hours = payload.duration_in_hours

        if payload.title is not None:
            course.title = payload.title
        if payload.description is not None:
            course.description = payload.description

        course_details.updated_at = datetime.utcnow()

        db.commit()

        return {
            "message": "Course details updated successfully",
            "course_details": {
                "course_id": course_details.course_id,
                "syllabus_summary": course_details.syllabus_summary,
                "syllabus_path": course_details.syllabus_path,
                "venue": course_details.venue,
                "start_date": course_details.start_date,
                "end_date": course_details.end_date,
                "start_time": course_details.start_time,
                "end_time": course_details.end_time,
                "duration_in_hours": course_details.duration_in_hours,
                "title": course.title,
                "description": course.description,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the course details"
        )

# ─── Endpoint: Get All Course Details ──────────────────────────────
@router.get("/courses/details")
def get_all_course_details(db: Session = Depends(get_db)):
    try:
        courses = db.query(Course).all()
        result = []
        for course in courses:
            details = db.query(CourseDetails).filter(CourseDetails.course_id == course.id).first()
            if details:
                result.append({
                    "course_id": course.id,
                    "title": course.title,
                    "description": course.description,
                    "mode": course.mode.value if hasattr(course.mode, "value") else str(course.mode),
                    "syllabus_summary": details.syllabus_summary,
                    "syllabus_path": details.syllabus_path,
                    "venue": details.venue,
                    "start_date": details.start_date,
                    "end_date": details.end_date,
                    "start_time": details.start_time,
                    "end_time": details.end_time,
                    "duration_in_hours": details.duration_in_hours,
                    "created_at": details.created_at,
                    "updated_at": details.updated_at,
                })
        return {"courses": result}
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching course details"
        )

# ─── Endpoint: Get Course Details By ID ──────────────────────────────
@router.get("/courses/{course_id}/details")
def get_course_details_by_id(course_id: int, db: Session = Depends(get_db)):
    try:
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        details = db.query(CourseDetails).filter(CourseDetails.course_id == course.id).first()
        if not details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course details not found"
            )
        return {
            "course_id": course.id,
            "title": course.title,
            "description": course.description,
            "mode": course.mode.value if hasattr(course.mode, "value") else str(course.mode),
            "syllabus_summary": details.syllabus_summary,
            "syllabus_path": details.syllabus_path,
            "venue": details.venue,
            "start_date": details.start_date,
            "end_date": details.end_date,
            "start_time": details.start_time,
            "end_time": details.end_time,
            "duration_in_hours": details.duration_in_hours,
            "created_at": details.created_at,
            "updated_at": details.updated_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching course details"
        )






