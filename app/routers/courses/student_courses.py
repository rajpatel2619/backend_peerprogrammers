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
    }


@router.get("/registed_courses/{user_id}")
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
        }
        for course in courses
    ]
