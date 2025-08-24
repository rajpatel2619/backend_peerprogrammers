from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from ...models.course_model import Courses
from ...connection.utility import get_db
from ...models.registration_model import CourseRegistration

router = APIRouter(tags=["Courses"])


@router.get("/courses/{course_id}")
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Courses).filter(Courses.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    return {
        "id": course.id,
        "title": course.title,
        "mode": course.mode,
        "creatorid": course.creatorid,
        "description": course.description,
        "price": course.price,
        "seats": course.seats,
        "start_date": course.start_date,
        "end_date": course.end_date,
        "syllabus_link": course.syllabus_link,
        "syllausContent": course.syllausContent,
        # "lecture_link": course.lecture_link,
        # "chatLink": course.chatLink,
        # "is_published": course.is_published,
        # "isVerified": course.isVerified,
        "isExtraRegistration": course.isExtraRegistration,
        "cover_photo": course.cover_photo,
        "co_mentors": course.co_mentors,
        "domains": course.domains,
        "created_at": course.created_at,
        "updated_at": course.updated_at,
        # Related mentors
        "mentors": [
            {
                "user_id": mentor.user_id,
                "role": mentor.role,
                "joined_at": mentor.joined_at,
                "name": (
                    f"{mentor.user.user_details.firstName} {mentor.user.user_details.lastName}"
                    if mentor.user and mentor.user.user_details
                    else None
                ),
                "email": (
                    mentor.user.user_details.email
                    if mentor.user and mentor.user.user_details
                    else None
                ),
            }
            for mentor in course.mentors
        ],
        # Related domain tags
        "domain_tags": [
            {"id": domain_tag.domain.id, "name": domain_tag.domain.name}
            for domain_tag in course.domain_tags
        ],
    }


@router.get("/courses_all_details/{course_id}")
def get_course_all_details(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Courses).filter(Courses.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Fetch registered students
    registrations = db.query(CourseRegistration).filter_by(course_id=course_id).all()
    students = []
    for reg in registrations:
        user = reg.user  # Assuming CourseRegistration.user → User
        if user and user.user_details:
            students.append({
                "user_id": user.id,
                "name": f"{user.user_details.firstName} {user.user_details.lastName}",
                "email": user.user_details.email,
                "registered_at": reg.payment_date,
                "transaction_id": reg.transaction_id,
                "fee_paid": reg.fee
            })

    return {
        "id": course.id,
        "title": course.title,
        "mode": course.mode,
        "creatorid": course.creatorid,
        "description": course.description,
        "price": course.price,
        "seats": course.seats,
        "start_date": course.start_date,
        "end_date": course.end_date,
        "syllabus_link": course.syllabus_link,
        "syllausContent": course.syllausContent,
        "lecture_link": course.lecture_link,
        "chatLink": course.chatLink,
        "is_published": course.is_published,
        "isVerified": course.isVerified,
        "isExtraRegistration": course.isExtraRegistration,
        "cover_photo": course.cover_photo,
        "co_mentors": course.co_mentors,
        "domains": course.domains,
        "created_at": course.created_at,
        "updated_at": course.updated_at,

        # Related mentors
        "mentors": [
            {
                "user_id": mentor.user_id,
                "role": mentor.role,
                "joined_at": mentor.joined_at,
                "name": (
                    f"{mentor.user.user_details.firstName} {mentor.user.user_details.lastName}"
                    if mentor.user and mentor.user.user_details
                    else None
                ),
                "email": (
                    mentor.user.user_details.email
                    if mentor.user and mentor.user.user_details
                    else None
                ),
            }
            for mentor in course.mentors
        ],

        # Related domain tags
        "domain_tags": [
            {"id": domain_tag.domain.id, "name": domain_tag.domain.name}
            for domain_tag in course.domain_tags
        ],

        # Registered students
        "students": students,
        "total_registered": len(students),
    }


@router.get("/registered_courses/{user_id}")
def get_registered_courses(user_id: int, db: Session = Depends(get_db)):
    registrations = db.query(CourseRegistration).filter_by(user_id=user_id).all()
    if not registrations:
        raise HTTPException(status_code=404, detail="No registrations found")

    course_ids = [reg.course_id for reg in registrations]

    courses = db.query(Courses).filter(Courses.id.in_(course_ids)).all()

    return [
        {
            "id": course.id,
            "title": course.title,
            "mode": course.mode,
            "start_date": course.start_date,
            "end_date": course.end_date,
            "domains": course.domains,
          
        }
        for course in courses
    ]


# ─── 3. Get Registered Students ───────────────────────────────────────────────────
@router.get("/students/{course_id}")
def get_registered_students(course_id: int, db: Session = Depends(get_db)):
    registrations = (
        db.query(CourseRegistration)
        .filter_by(course_id=course_id)
        .all()
    )

    if not registrations:
        raise HTTPException(status_code=404, detail="No registrations found")

    students = []
    for reg in registrations:
        user = reg.user  # Assuming a relationship exists: CourseRegistration.user → User
        if user and user.user_details:
            students.append({
                "user_id": user.id,
                "name": f"{user.user_details.firstName} {user.user_details.lastName}",
                "email": user.user_details.email,
                "registered_at": reg.payment_date,
                "transaction_id": reg.transaction_id,
                "fee_paid": reg.fee
            })

    return {
        "course_id": course_id,
        "students": students,
        "total": len(students)
    }

from datetime import date
from sqlalchemy import or_


@router.get("/all_courses")
def get_all_courses(db: Session = Depends(get_db)):
    try:
        today = date.today()

        courses = (
            db.query(Courses)
            .filter(Courses.is_published == True)
            # .filter(or_(Courses.end_date == None, Courses.end_date >= today))
            .order_by(Courses.created_at.desc())
            .all()
        )

        result = []

        for course in courses:
            creator = course.creator  # Assuming Courses.creator → User
            creator_name = (
                f"{creator.user_details.firstName} {creator.user_details.lastName}"
                if creator and creator.user_details else None
            )

            result.append({
                "id": course.id,
                "title": course.title,
                "mode": course.mode,
                "cover_photo": course.cover_photo,
                "syllabus_link": course.syllabus_link,
                "creator": {
                    "id": course.creatorid,
                    "name": creator_name
                },
                "price": course.price,
                "isVerified": course.isVerified,
                "seats": course.seats,
                "start_date": str(course.start_date) if course.start_date else None,
                "end_date": str(course.end_date) if course.end_date else None,
                "domains": [d.domain.name for d in course.domain_tags],
                # "domain_ids": [d.domain_id for d in course.domain_tags],
            })

        return {"success": True, "courses": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch courses: {str(e)}")




@router.get("/all_courses_short")
def get_all_courses_short(db: Session = Depends(get_db)):
    try:
        today = date.today()

        courses = (
            db.query(Courses)
            .filter(Courses.is_published == True)
            # .filter(or_(Courses.end_date == None, Courses.end_date >= today))
            .order_by(Courses.created_at.desc())
            .all()
        )

        result = []

        for course in courses:
            creator = course.creator  # Assuming Courses.creator → User
            creator_name = (
                f"{creator.user_details.firstName} {creator.user_details.lastName}"
                if creator and creator.user_details else None
            )

            result.append({
                "id": course.id,
                "title": course.title,
                # "mode": course.mode,
                # "cover_photo": course.cover_photo,
                # "syllabus_link": course.syllabus_link,
                "creator": {
                    "id": course.creatorid,
                    "name": creator_name
                },
                "price": course.price,
                "isVerified": course.isVerified,
                # "seats": course.seats,
                "start_date": str(course.start_date) if course.start_date else None,
                # "end_date": str(course.end_date) if course.end_date else None,
                # "domains": [d.domain.name for d in course.domain_tags],
                # "domain_ids": [d.domain_id for d in course.domain_tags],
            })

        return {"success": True, "courses": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch courses: {str(e)}")
