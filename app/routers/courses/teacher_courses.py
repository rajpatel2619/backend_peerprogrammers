from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import inspect
from datetime import datetime
from ...connection.utility import get_db
from ...schemas.course_schema import *
from ...models.course_model import *
from ...models.user_model import *

router = APIRouter()




@router.put("/update-course/{user_id}/{course_id}")
def update_course(user_id: int, course_id: int, payload: dict, db: Session = Depends(get_db)):
    course = db.query(IndividualCourse).filter(IndividualCourse.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.creatorid != user_id:
        raise HTTPException(status_code=403, detail="Only creator can update this course")

    # Map payload to course fields dynamically
    updatable_fields = [
        "title", "mode", "start_date", "end_date", "description",
        "syllabus_link", "daily_meeting_link", "lecture_link", "cover_photo",
        "price", "is_published",
        "basic_seats", "basic_price", "basic_whatsapp", "basic_meeting_link",
        "premium_seats", "premium_price", "premium_whatsapp", "premium_meeting_link",
        "ultra_seats", "ultra_price", "ultra_whatsapp", "ultra_meeting_link",
        "co_mentors"
    ]

        # Update basic course fields
    for field in updatable_fields:
        if field in payload:
            setattr(course, field, payload[field])

    # Handle co_mentors from creator_ids
    if "creator_ids" in payload:
        co_mentors = [uid for uid in payload["creator_ids"] if uid != user_id]
        course.co_mentors = ",".join(str(uid) for uid in co_mentors)

    # Handle domains update
    if "domains" in payload:
        db.query(CourseDomain).filter_by(course_id=course.id).delete()
        for domain_id in payload["domains"]:
            db.add(CourseDomain(course_id=course.id, domain_id=int(domain_id)))

    db.commit()
    db.refresh(course)

    return {
        "success": True,
        "message": "Course updated successfully",
        "course_id": course.id
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
def create_course(payload: dict, db: Session = Depends(get_db)):
    try:
        # Prepare co_mentors string (optional)
        co_mentors_str = ",".join(str(uid) for uid in payload.get("creator_ids", [])).strip(",")

        # Create course object based on mode
        if payload["mode"].lower() == "live":
            course = IndividualCourse(
                creatorid=payload["userId"],
                title=payload["title"],
                mode=payload["mode"],
                start_date=payload.get("start_date"),
                end_date=payload.get("end_date"),
                co_mentors=co_mentors_str,
                description=payload.get("description"),
                syllabus_link=payload.get("syllabusFile"),
                daily_meeting_link=payload.get("daily_meeting_link"),
                is_published=payload.get("is_published", False),
                cover_photo=payload.get("coverPhoto"),
                lecture_link=payload.get("lecture_link"),
                basic_seats=payload["basic_plan"]["seats"],
                basic_price=payload["basic_plan"]["price"],
                basic_whatsapp=payload["basic_plan"]["whatsapp"],
                basic_meeting_link=payload["basic_plan"].get("meeting_link"),
                premium_seats=payload["premium_plan"]["seats"],
                premium_price=payload["premium_plan"]["price"],
                premium_whatsapp=payload["premium_plan"]["whatsapp"],
                premium_meeting_link=payload["premium_plan"].get("meeting_link"),
                ultra_seats=payload["ultra_plan"]["seats"],
                ultra_price=payload["ultra_plan"]["price"],
                ultra_whatsapp=payload["ultra_plan"]["whatsapp"],
                ultra_meeting_link=payload["ultra_plan"].get("meeting_link"),
            )
        else:  # Recorded mode
            course = IndividualCourse(
                creatorid=payload["userId"],
                title=payload["title"],
                mode=payload["mode"],
                start_date=payload.get("start_date"),
                end_date=payload.get("end_date"),
                co_mentors=co_mentors_str,
                description=payload.get("description"),
                syllabus_link=payload.get("syllabusFile"),
                daily_meeting_link=payload.get("daily_meeting_link"),
                is_published=payload.get("is_published", False),
                cover_photo=payload.get("coverPhoto"),
                lecture_link=payload.get("lecture_link"),
                price=payload.get("price"),
            )

        db.add(course)
        db.flush()  # To get course.id before commit

        # Save mentors
        for uid in payload.get("creator_ids", []):
            if not db.query(User).filter_by(id=uid).first():
                raise HTTPException(status_code=400, detail=f"User ID {uid} does not exist")
            db.add(CourseMentor(course_id=course.id, user_id=uid, role="Mentor"))

        # Save domains (by resolving domain names to domain_ids)
        for domain_id in payload.get("domains", []):
            domain_obj = db.query(DomainTag).filter_by(id=domain_id).first()
            if not domain_obj:
                raise HTTPException(status_code=400, detail=f"Domain ID '{domain_id}' not found")
            db.add(CourseDomain(course_id=course.id, domain_id=domain_id))


        db.commit()
        db.refresh(course)

        # Build response
        return {
            "success": True,
            "course": {
                "id": course.id,
                "title": course.title,
                "mode": course.mode,
                "creatorid": course.creatorid,
                "is_published": course.is_published,
                "syllabus_link": course.syllabus_link,
                "co_mentors": course.co_mentors,
                "cover_photo": course.cover_photo,
                "description": course.description,
                "start_date": str(course.start_date) if course.start_date else None,
                "end_date": str(course.end_date) if course.end_date else None,
                "daily_meeting_link": course.daily_meeting_link,
                "lecture_link": course.lecture_link,
                "basic_plan": (
                    {
                        "seats": course.basic_seats,
                        "price": course.basic_price,
                        "whatsapp": course.basic_whatsapp,
                        "meeting_link": course.basic_meeting_link,
                    }
                    if course.mode.lower() == "live"
                    else None
                ),
                "premium_plan": (
                    {
                        "seats": course.premium_seats,
                        "price": course.premium_price,
                        "whatsapp": course.premium_whatsapp,
                        "meeting_link": course.premium_meeting_link,
                    }
                    if course.mode.lower() == "live"
                    else None
                ),
                "ultra_plan": (
                    {
                        "seats": course.ultra_seats,
                        "price": course.ultra_price,
                        "whatsapp": course.ultra_whatsapp,
                        "meeting_link": course.ultra_meeting_link,
                    }
                    if course.mode.lower() == "live"
                    else None
                ),
                "price": course.price if course.mode.lower() == "recorded" else None,
                "domains": [d.domain.name for d in course.domain_tags],
                "creator_ids": [m.user_id for m in course.mentors],
                "created_at": course.created_at.isoformat(),
                "updated_at": course.updated_at.isoformat(),
            },
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


