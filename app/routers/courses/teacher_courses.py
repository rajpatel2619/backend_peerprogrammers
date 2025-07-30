import os
import shutil
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from ...connection.utility import get_db
from ...schemas.course_schema import *
from ...models.course_model import *
from ...models.user_model import *

# Initialize Router and Environment
router = APIRouter()
load_dotenv()
UPLOAD_DIR = os.getenv("UPLOAD_DIR")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Create Course Endpoint
@router.post("/create-course")
def create_course(
    userId: int = Form(...),
    title: str = Form(...),
    mode: str = Form(...),
    seats: int = Form(...),
    chat_link: str = Form(...),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    syllabus_content: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    is_published: Optional[bool] = Form(False),
    is_extra_registration: Optional[bool] = Form(False),
    co_mentor_ids: Optional[str] = Form(""),
    creator_ids: Optional[str] = Form(""),
    domain_ids: Optional[str] = Form(""),
    cover_photo: UploadFile = File(...),
    syllabus_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        cover_filename = f"{userId}_{timestamp}_{os.path.basename(cover_photo.filename)}"
        syllabus_filename = f"{userId}_{timestamp}_{os.path.basename(syllabus_file.filename)}"

        cover_path = os.path.join(UPLOAD_DIR, cover_filename)
        syllabus_path = os.path.join(UPLOAD_DIR, syllabus_filename)

        with open(cover_path, "wb") as f:
            shutil.copyfileobj(cover_photo.file, f)
        with open(syllabus_path, "wb") as f:
            shutil.copyfileobj(syllabus_file.file, f)

        cover_url = f"https://localhost:8283/uploads/{cover_filename}"
        syllabus_url = f"https://localhost:8283/uploads/{syllabus_filename}"

        course = Courses(
            creatorid=userId,
            title=title,
            mode=mode,
            seats=seats,
            chatLink=chat_link,
            start_date=start_date,
            end_date=end_date,
            description=description,
            syllausContent=syllabus_content,
            syllabus_link=syllabus_url,
            cover_photo=cover_url,
            lecture_link=None,
            price=price,
            is_published=is_published,
            isExtraRegistration=is_extra_registration,
            co_mentors=",".join(co_mentor_ids.split(",")) if co_mentor_ids else ""
        )

        db.add(course)
        db.flush()

        for uid in creator_ids.split(","):
            if uid.strip():
                db.add(CourseMentor(course_id=course.id, user_id=int(uid), role="Mentor"))

        for domain_id in domain_ids.split(","):
            if domain_id.strip():
                db.add(CourseDomain(course_id=course.id, domain_id=int(domain_id)))

        db.commit()
        db.refresh(course)

        return {
            "success": True,
            "message": "Course created",
            "course": {
                "id": course.id,
                "cover_photo": cover_url,
                "syllabus_link": syllabus_url
            }
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Course creation failed: {str(e)}")

# Update Course Endpoint
@router.put("/update-course/{user_id}/{course_id}")
def update_course(
    user_id: int,
    course_id: int,
    payload: dict,
    cover_photo: Optional[UploadFile] = File(None),
    syllabus_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    course = db.query(Courses).filter(Courses.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.creatorid != user_id:
        raise HTTPException(status_code=403, detail="Only the creator can update this course")

    updatable_fields = [
        "title", "mode", "start_date", "end_date", "description",
        "syllabus_link", "syllausContent", "lecture_link", "cover_photo",
        "price", "seats", "chatLink", "co_mentors"
    ]

    for field in updatable_fields:
        if field in payload:
            setattr(course, field, payload[field])

    course.isVerified = False

    if cover_photo:
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        cover_filename = f"{user_id}_{timestamp}_{os.path.basename(cover_photo.filename)}"
        cover_path = os.path.join(UPLOAD_DIR, cover_filename)
        with open(cover_path, "wb") as f:
            shutil.copyfileobj(cover_photo.file, f)
        course.cover_photo = f"https://localhost:8283/uploads/{cover_filename}"

    if syllabus_file:
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        syllabus_filename = f"{user_id}_{timestamp}_{os.path.basename(syllabus_file.filename)}"
        syllabus_path = os.path.join(UPLOAD_DIR, syllabus_filename)
        with open(syllabus_path, "wb") as f:
            shutil.copyfileobj(syllabus_file.file, f)
        course.syllabus_link = f"https://localhost:8283/uploads/{syllabus_filename}"

    if "creator_ids" in payload:
        co_mentors = [uid for uid in payload["creator_ids"] if uid != user_id]
        course.co_mentors = ",".join(str(uid) for uid in co_mentors)

        db.query(CourseMentor).filter_by(course_id=course.id).delete()
        for mentor_id in payload["creator_ids"]:
            db.add(CourseMentor(course_id=course.id, user_id=mentor_id, role="Mentor"))

    if "domain_ids" in payload:
        db.query(CourseDomain).filter_by(course_id=course.id).delete()
        for domain_id in payload["domain_ids"]:
            db.add(CourseDomain(course_id=course.id, domain_id=int(domain_id)))

    db.commit()
    db.refresh(course)

    return {
        "success": True,
        "message": "Course updated successfully",
        "course_id": course.id
    }



# Unpublish a Course
@router.post("/unpublish-courses/{user_id}/{course_id}")
def unpublish_course(user_id: int, course_id: int, db: Session = Depends(get_db)):
    course = db.query(Courses).filter(Courses.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.creatorid != user_id:
        raise HTTPException(status_code=403, detail="User is not the creator of this course")

    course.is_published = False
    db.commit()

    return {
        "success": True,
        "message": "Course unpublished successfully",
        "course_id": course.id
    }

# Publish a Course
@router.post("/publish-courses/{user_id}/{course_id}")
def publish_course(user_id: int, course_id: int, db: Session = Depends(get_db)):
    course = db.query(Courses).filter(Courses.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.creatorid != user_id:
        raise HTTPException(status_code=403, detail="User is not the creator of this course")

    course.is_published = True
    db.commit()

    return {
        "success": True,
        "message": "Course published successfully",
        "course_id": course.id
    }



@router.get("/all-courses")
def get_all_courses(db: Session = Depends(get_db)):
    try:
        courses = db.query(Courses).all()
        result = []

        for course in courses:
            result.append({
                "id": course.id,
                "title": course.title,
                "mode": course.mode,
                "creatorid": course.creatorid,
                "description": course.description,
                "cover_photo": course.cover_photo,
                "syllabus_link": course.syllabus_link,
                "co_mentors": course.co_mentors,
                "lecture_link": course.lecture_link,
                "chatLink": course.chatLink,
                "price": course.price,
                "seats": course.seats,
                "start_date": str(course.start_date) if course.start_date else None,
                "end_date": str(course.end_date) if course.end_date else None,
                "is_published": course.is_published,
                "created_at": course.created_at.isoformat(),
                "updated_at": course.updated_at.isoformat(),
                "creator_ids": [m.user_id for m in course.mentors],
                "domains": [d.domain.name for d in course.domain_tags],
            })

        return {
            "success": True,
            "courses": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch courses: {str(e)}")


@router.get("/courses/by-user/{user_id}")
def get_courses_by_user(user_id: int, db: Session = Depends(get_db)):
    try:
        creator_course_ids = db.query(Courses.id).filter(Courses.creatorid == user_id)
        mentor_course_ids = db.query(CourseMentor.course_id).filter(CourseMentor.user_id == user_id)

        all_ids = {cid for (cid,) in creator_course_ids.union(mentor_course_ids).all()}
        courses = db.query(Courses).filter(Courses.id.in_(all_ids)).all()

        result = []
        for c in courses:
            result.append({
                "id": c.id,
                "title": c.title,
                "mode": c.mode,
                "creatorid": c.creatorid,
                "description": c.description,
                "cover_photo": c.cover_photo,
                "syllabus_link": c.syllabus_link,
                "co_mentors": c.co_mentors,
                "lecture_link": c.lecture_link,
                "chatLink": c.chatLink,
                "price": c.price,
                "seats": c.seats,
                "start_date": str(c.start_date) if c.start_date else None,
                "end_date": str(c.end_date) if c.end_date else None,
                "is_published": c.is_published,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
                "creator_ids": [m.user_id for m in c.mentors],
                "domains": [d.domain.name for d in c.domain_tags],
            })

        return {
            "success": True,
            "courses": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch courses: {str(e)}")
