import shutil
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import inspect
from datetime import datetime
from ...connection.utility import get_db
from ...schemas.course_schema import *
from ...models.course_model import *
from ...models.user_model import *
import os
from dotenv import load_dotenv


router = APIRouter()



load_dotenv()  # Load from .env

UPLOAD_DIR = os.getenv("UPLOAD_DIR")


# Make sure the directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload-course-file/")
def upload_course_file(file: UploadFile = File(...), userId: int = None):
    if not userId:
        raise HTTPException(status_code=400, detail="userId is required")

    # Extract only the file name (no directories)
    original_filename = os.path.basename(file.filename)

    # Create unique filename
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    filename = f"{userId}_{timestamp}_{original_filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    # Save the file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    public_url = f"https://localhost:8283/uploads/{filename}"

    return {
        "message": "File uploaded successfully",
        "url": public_url
    }


@router.delete("/delete-course-file/")
def delete_course_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        os.remove(file_path)
        return {"message": "File deleted successfully", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


@router.put("/update-course/{user_id}/{course_id}")
def update_course(user_id: int, course_id: int, payload: dict, db: Session = Depends(get_db)):
    course = db.query(Courses).filter(Courses.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.creatorid != user_id:
        raise HTTPException(status_code=403, detail="Only the creator can update this course")

    # Fields allowed to be updated
    updatable_fields = [
        "title", "mode", "start_date", "end_date", "description",
        "syllabus_link", "syllausContent", "lecture_link", "cover_photo",
        "price", "seats", "chatLink", "co_mentors"
    ]

    # Update course fields
    for field in updatable_fields:
        if field in payload:
            setattr(course, field, payload[field])
            
    course.isVerified = False

    # Handle co_mentors from creator_ids (if provided)
    if "creator_ids" in payload:
        co_mentors = [uid for uid in payload["creator_ids"] if uid != user_id]
        course.co_mentors = ",".join(str(uid) for uid in co_mentors)

        # Update CourseMentor entries
        db.query(CourseMentor).filter_by(course_id=course.id).delete()
        for mentor_id in payload["creator_ids"]:
            db.add(CourseMentor(course_id=course.id, user_id=mentor_id, role="Mentor"))

    # Handle domain updates
    if "domain_ids" in payload:
        db.query(CourseDomain).filter_by(course_id=course.id).delete()
        for domain_id in payload["domain_ids"]:
            db.add(CourseDomain(course_id=course.id, domain_id=int(domain_id)))

    db.commit()
    db.refresh(course)

    return {
        "success": True,
        "message": "Course updated successfully",
        "course_id": course
    }



@router.post("/unpublish-courses/{user_id}/{course_id}")
def unpublish_course(user_id: int, course_id: int, db: Session = Depends(get_db)):
    course = db.query(IndividualCourse).filter(IndividualCourse.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.creatorid != user_id:
        raise HTTPException(status_code=403, detail="User is not the creator of this course")

    course.is_published = False
    db.commit()
    return {"success": True, "message": "Course unpublished", "course_id": course_id}


@router.post("/publish-courses/{user_id}/{course_id}")
def publish_course(user_id: int, course_id: int, db: Session = Depends(get_db)):
    course = db.query(IndividualCourse).filter(IndividualCourse.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.creatorid != user_id:
        raise HTTPException(status_code=403, detail="User is not the creator of this course")

    course.is_published = True
    db.commit()
    return {"success": True, "message": "Course published", "course_id": course_id}


@router.get("/all-courses")
def get_all_courses(db: Session = Depends(get_db)):
    try:
        courses = db.query(IndividualCourse).all()
        all_courses = []

        for course in courses:
            course_data = {
                "id": course.id,
                "title": course.title,
                "mode": course.mode,
                "creatorid": course.creatorid,
                "is_published": course.is_published,
                "syllabus_link": course.syllabus_link,
                "co_mentors": course.co_mentors,
                "cover_photo": course.cover_photo,
                "description": course.description,
                "start_date": str(course.start_date),
                "end_date": str(course.end_date),
                "daily_meeting_link": course.daily_meeting_link,
                "lecture_link": course.lecture_link,
                "price": course.price,
                "basic_plan": {
                    "seats": course.basic_seats,
                    "price": course.basic_price,
                    "whatsapp": course.basic_whatsapp,
                    "meeting_link": course.basic_meeting_link,
                },
                "premium_plan": {
                    "seats": course.premium_seats,
                    "price": course.premium_price,
                    "whatsapp": course.premium_whatsapp,
                    "meeting_link": course.premium_meeting_link,
                },
                "ultra_plan": {
                    "seats": course.ultra_seats,
                    "price": course.ultra_price,
                    "whatsapp": course.ultra_whatsapp,
                    "meeting_link": course.ultra_meeting_link,
                },
                "domains": [d.domain for d in course.domain_tags],
                "creator_ids": [m.user_id for m in course.mentors],
                "created_at": course.created_at.isoformat(),
                "updated_at": course.updated_at.isoformat(),
            }
            all_courses.append(course_data)

        return {"success": True, "courses": all_courses}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch courses: {str(e)}")

@router.get("/courses/{course_id}")
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(IndividualCourse).filter(IndividualCourse.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    return {
        "id": course.id,
        "title": course.title,
        "mode": course.mode,
        "creatorid": course.creatorid,
        "is_published": course.is_published,
        "syllabus_link": course.syllabus_link,
        "co_mentors": course.co_mentors,
        "cover_photo": course.cover_photo,
        "description": course.description,
        "start_date": str(course.start_date),
        "end_date": str(course.end_date),
        "daily_meeting_link": course.daily_meeting_link,
        "lecture_link": course.lecture_link,
        "price": course.price,
        "basic_plan": {
            "seats": course.basic_seats,
            "price": course.basic_price,
            "whatsapp": course.basic_whatsapp,
            "meeting_link": course.basic_meeting_link,
        },
        "premium_plan": {
            "seats": course.premium_seats,
            "price": course.premium_price,
            "whatsapp": course.premium_whatsapp,
            "meeting_link": course.premium_meeting_link,
        },
        "ultra_plan": {
            "seats": course.ultra_seats,
            "price": course.ultra_price,
            "whatsapp": course.ultra_whatsapp,
            "meeting_link": course.ultra_meeting_link,
        },
        "domains": [d.domain.id for d in course.domain_tags],
        "creator_ids": [a.user_id for a in course.mentors],
        "created_at": course.created_at.isoformat(),
        "updated_at": course.updated_at.isoformat(),
    }

@router.get("/courses/by-user/{user_id}")
def get_courses_by_user(user_id: int, db: Session = Depends(get_db)):
    try:
        # Collect all course IDs where user is a creator or mentor
        creator_course_ids = (
            db.query(IndividualCourse.id)
            .filter(IndividualCourse.creatorid == user_id)
        )

        mentor_course_ids = (
            db.query(CourseMentor.course_id)
            .filter(CourseMentor.user_id == user_id)
        )

        # Merge and deduplicate using set union
        all_course_ids = {id for (id,) in creator_course_ids.union(mentor_course_ids).all()}

        # Fetch actual course objects
        courses = (
            db.query(IndividualCourse)
            .filter(IndividualCourse.id.in_(all_course_ids))
            .all()
        )

        result = [
            {
                "id": c.id,
                "title": c.title,
                "mode": c.mode,
                "creatorid": c.creatorid,
                "description": c.description,
                "start_date": str(c.start_date) if c.start_date else None,
                "end_date": str(c.end_date) if c.end_date else None,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
                "is_published":c.is_published,
            }
            for c in courses
        ]

        return {"success": True, "courses": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch courses: {str(e)}")

@router.post("/create-course")
def create_course(payload: dict,file: UploadFile = File(...),  db: Session = Depends(get_db)):
    try:
        # Prepare co_mentors string (optional)
        co_mentors_str = ",".join(str(uid) for uid in payload.get("co_mentor_ids", [])).strip(",")

        course = Courses(
            creatorid=payload["userId"],
            title=payload["title"],
            mode=payload["mode"],
            start_date=payload.get("start_date"),
            end_date=payload.get("end_date"),
            co_mentors=co_mentors_str,
            description=payload.get("description"),
            syllabus_link=payload.get("syllabus_link"),
            syllausContent=payload.get("syllabus_content"),
            is_published=payload.get("is_published", False),
            cover_photo=payload.get("cover_photo"),
            lecture_link=payload.get("lecture_link"),
            seats=payload["seats"],
            chatLink=payload["chat_link"],
            price=payload.get("price"),
            isExtraRegistration=payload.get("is_extra_registration", False),
        )

        db.add(course)
        db.flush()  # To get course.id before commit

        # Save mentors
        for uid in payload.get("creator_ids", []):
            user = db.query(User).filter_by(id=uid).first()
            if not user:
                raise HTTPException(status_code=400, detail=f"User ID {uid} does not exist")

            db.add(CourseMentor(course_id=course.id, user_id=uid, role="Mentor"))

        # Save domain tags
        for domain_id in payload.get("domain_ids", []):
            domain = db.query(DomainTag).filter_by(id=domain_id).first()
            if not domain:
                raise HTTPException(status_code=400, detail=f"Domain ID {domain_id} not found")

            db.add(CourseDomain(course_id=course.id, domain_id=domain_id))

        db.commit()
        db.refresh(course)

        return {
            "success": True,
            "course": course
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Course creation failed: {str(e)}")


## DOMAIN RELATED ###########################################

@router.post("/add-domain-tag")
def add_domain_tag(payload: dict, db: Session = Depends(get_db)):
    name = payload["name"]  
    existing = db.query(DomainTag).filter(DomainTag.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Domain tag already exists")

    new_tag = DomainTag(name=name)
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)

    return {
        "success": True,
        "message": "Domain tag added successfully",
        "tag_id": new_tag.id,
        "tag_name": new_tag.name
    }


@router.get("/all-domain-tags")
def get_all_domain_tags(db: Session = Depends(get_db)):
    tags = db.query(DomainTag).order_by(DomainTag.name).all()

    return {
        "success": True,
        "total": len(tags),
        "tags": [{"id": tag.id, "name": tag.name} for tag in tags]
    }


