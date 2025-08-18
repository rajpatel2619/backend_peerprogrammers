from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from ...models.course_model import Courses
from ...connection.utility import get_db
from ...models.registration_model import CourseRegistration
from fastapi import status

router = APIRouter()



@router.get("/unverified_courses")
def get_unverified_courses(db: Session = Depends(get_db)):
    unverified_courses = db.query(Courses).filter(Courses.isVerified == False).all()

    if not unverified_courses:
        return {"success": True, "courses": [], "message": "No unverified courses found."}

    result = []

    for course in unverified_courses:
        creator = course.creator  # Assuming Courses.creator → User relationship exists
        creator_name = (
            f"{creator.user_details.firstName} {creator.user_details.lastName}"
            if creator and creator.user_details else None
        )

        result.append({
            "id": course.id,
            "title": course.title,
            "mode": course.mode,
            "isVerified": course.isVerified,
            "cover_photo": course.cover_photo,
            "syllabus_link": course.syllabus_link,
            "isVerified":course.isVerified,
            "creator": {
                "id": course.creatorid,
                "name": creator_name
            },
            "price": course.price,
            "seats": course.seats,
            "start_date": str(course.start_date) if course.start_date else None,
            "end_date": str(course.end_date) if course.end_date else None,
            "domains": [d.domain.name for d in course.domain_tags],
            "domain_ids": [d.domain_id for d in course.domain_tags],
        })

    return {"success": True, "courses": result}


@router.get("/verified_courses")
def get_verified_courses(db: Session = Depends(get_db)):
    verified_courses = db.query(Courses).filter(Courses.isVerified == True).all()

    if not verified_courses:
        return {"success": True, "courses": [], "message": "No verified courses found."}

    result = []

    for course in verified_courses:
        creator = course.creator  # Assuming Courses.creator → User relationship exists
        creator_name = (
            f"{creator.user_details.firstName} {creator.user_details.lastName}"
            if creator and creator.user_details else None
        )

        result.append({
            "id": course.id,
            "title": course.title,
            "mode": course.mode,
            "isVerified": course.isVerified,
            "cover_photo": course.cover_photo,
            "syllabus_link": course.syllabus_link,
            "creator": {
                "id": course.creatorid,
                "name": creator_name
            },
            "price": course.price,
            "seats": course.seats,
            "start_date": str(course.start_date) if course.start_date else None,
            "end_date": str(course.end_date) if course.end_date else None,
            "domains": [d.domain.name for d in course.domain_tags],
            "domain_ids": [d.domain_id for d in course.domain_tags],
        })

    return {"success": True, "courses": result}


@router.put("/verify_course/{course_id}", status_code=status.HTTP_200_OK)
def toggle_verify_course(course_id: int, db: Session = Depends(get_db)):
    # Fetch the course
    course = db.query(Courses).filter(Courses.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Toggle the isVerified field
    course.isVerified = not course.isVerified
    
    db.commit()
    db.refresh(course)
    
    return {
        "success": True,
        "message": f"Course verification toggled to {course.isVerified}.",
        "course_id": course.id,
        "isVerified": course.isVerified
    }


@router.get("/course_verification_status/{course_id}")
def get_course_verification_status(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Courses).filter(Courses.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    return {
        "course_id": course.id,
        "isVerified": course.isVerified
    }




@router.get("/courses/by-user/{user_id}")
def get_courses_by_user(user_id: int, db: Session = Depends(get_db)):
    try:
        creator_courses = db.query(Courses).filter(Courses.creatorid == user_id).all()

        return {
            "success": True,
            "courses": [course for course in creator_courses]
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }
