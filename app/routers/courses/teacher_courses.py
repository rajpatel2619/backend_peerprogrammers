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
        "domains": [d.domain for d in course.domain_tags],
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
            }
            for c in courses
        ]

        return {"success": True, "courses": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch courses: {str(e)}")



@router.post("/create-course")
def create_course(payload: dict, db: Session = Depends(get_db)):
    try:
        # Prepare string fields
        domains_str = ",".join(payload.get("domains", [])).strip(",")
        co_mentors_str = ",".join(
            str(uid) for uid in payload.get("creator_ids", [])
        ).strip(",")

        # Create course object based on mode
        if payload["mode"].lower() == "live":
            course = IndividualCourse(
                creatorid=payload["userId"],
                title=payload["title"],
                mode=payload["mode"],
                start_date=payload.get("start_date"),
                end_date=payload.get("end_date"),
                domains=domains_str,
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
        else:
            course = IndividualCourse(
                creatorid=payload["userId"],
                title=payload["title"],
                mode=payload["mode"],
                start_date=payload.get("start_date"),
                end_date=payload.get("end_date"),
                domains=domains_str,
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
        db.flush()  # Get course.id before commit

        # Save mentors
        for uid in payload.get("creator_ids", []):
            if not db.query(User).filter_by(id=uid).first():
                raise HTTPException(
                    status_code=400, detail=f"User ID {uid} does not exist"
                )
            db.add(CourseMentor(course_id=course.id, user_id=uid, role="Mentor"))

        # Save domains
        for domain in payload.get("domains", []):
            db.add(CourseDomain(course_id=course.id, domain=domain))

        db.commit()
        db.refresh(course)

        # Construct response
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
                "domains": [d.domain for d in course.domain_tags],
                "creator_ids": [m.user_id for m in course.mentors],
                "created_at": course.created_at.isoformat(),
                "updated_at": course.updated_at.isoformat(),
            },
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Course creation failed: {str(e)}")


# @router.post("/fetch-courses")
# def fetch_courses(payload: dict, db: Session = Depends(get_db)):
#     try:
#         inspector = inspect(db.get_bind())

#         if "courses_1" not in inspector.get_table_names() or "course_details_1" not in inspector.get_table_names():
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="One or more required tables do not exist",
#             )

#         user_id = payload.get("id")
#         if not user_id:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="User ID is required in payload"
#             )


#         # Filter by creatorid
#         courses = db.query(Course).filter(Course.creatorid == user_id).all()
#         course_details = db.query(CourseDetails).all()

#         details_map = {cd.course_id: cd for cd in course_details}

#         result = []
#         for course in courses:
#             detail = details_map.get(course.id)
#             result.append({
#                 "id": course.id,
#                 "title": course.title,
#                 "category": course.category,
#                 "type": course.type,
#                 "creator_id": course.creatorid,
#                 "is_published": course.is_published,
#                 "syllabus_link": detail.syllabus_link if detail else None,
#                 "co_mentors": detail.co_mentors if detail else None,
#             })

#         return {
#             "message": "Courses fetched successfully.",
#             "courses": result
#         }

#     except Exception as e:
#         print(f"Error fetching courses: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to fetch courses"
#         )


# class CourseDetailsSchema(BaseModel):
#     course_id: int
#     syllabus_link: str
#     creatorsIds_str: str

# @router.post("/create-course")
# def course_details(payload: CourseDetailsSchema, db: Session = Depends(get_db)):
#     try:
#         inspector = inspect(db.get_bind())
#         if "course_details_1" not in inspector.get_table_names():
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="The 'course_details_1' table does not exist in the database",
#             )

#         new_course = CourseDetails(
#             course_id=payload.course_id,
#             syllabus_link=payload.syllabus_link,
#             co_mentors=payload.creatorsIds_str,
#             created_at=datetime.utcnow(),
#             updated_at=datetime.utcnow(),
#         )

#         db.add(new_course)
#         db.commit()
#         db.refresh(new_course)

#         return {
#             "message": "Course details created successfully.",
#             "course_details": {
#                 "id": new_course.id,
#                 "course_id": new_course.course_id,
#                 "syllabus_link": new_course.syllabus_link,
#                 "co_mentors": new_course.co_mentors,
#             },
#         }

#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"An error occurred: {e}")
#         db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="An error occurred while creating course details",
#         )


# class InitCourse(BaseModel):
#     creatorid: int
#     title: str
#     category: str
#     type: str


# @router.post("/init-course")
# def init_course(payload: InitCourse, db: Session = Depends(get_db)):
#     try:
#         inspector = inspect(db.get_bind())
#         if "courses_1" not in inspector.get_table_names():
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="The 'courses_1' table does not exist in the database",
#             )

#         new_course = Course(
#             creatorid=payload.creatorid,
#             title=payload.title,
#             category=payload.category,
#             type=payload.type,
#             created_at=datetime.utcnow(),
#             updated_at=datetime.utcnow(),
#         )

#         db.add(new_course)
#         db.commit()
#         db.refresh(new_course)

#         return {
#             "message": "Course created successfully.",
#             "course": {
#                 "id": new_course.id,
#                 "title": new_course.title,
#                 "category": new_course.category,
#                 "type": new_course.type,
#                 "creator_id": new_course.creatorid,
#                 "is_published": new_course.is_published,
#             },
#         }

#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"An error occurred: {e}")
#         db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="An error occurred while creating the course",
#         )


# @router.post("/courses")
# def create_course(payload: CourseCreate, db: Session = Depends(get_db)):
#     try:
#         # ✅ Check if 'courses' table exists
#         inspector = inspect(db.get_bind())
#         if "courses" not in inspector.get_table_names():
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="The 'courses' table does not exist in the database",
#             )

#         new_course = Course(
#             title=payload.title,
#             description=payload.description,
#             mode=CourseMode[payload.mode.value.lower()],
#             created_at=datetime.utcnow(),
#             updated_at=datetime.utcnow(),
#             is_active=True,
#         )
#         db.add(new_course)
#         # db.refresh(new_course)
#         db.flush()  # <-- Flush here to assign new_course.id

#         # Create course details with default values
#         new_course_details = CourseDetails(
#             course_id=new_course.id,  # Generate a unique course_id
#             syllabus_summary="Default syllabus summary",
#             syllabus_path="default/path",
#             venue="Default venue",
#             start_date=datetime.utcnow().date(),
#             end_date=datetime.utcnow().date(),
#             start_time=datetime.utcnow().time(),
#             end_time=datetime.utcnow().time(),
#             duration_in_hours=1,
#             created_at=datetime.utcnow(),
#             updated_at=datetime.utcnow(),
#         )

#         db.add(new_course_details)
#         # db.refresh(new_course_details)

#         # Add course authors
#         for creator in payload.creator_ids:
#             course_author = CourseAuthor(
#                 course_id=new_course.id,
#                 user_id=creator,
#                 role="Lead",  # You can customize the role as needed
#                 joined_at=datetime.utcnow(),
#             )
#             db.add(course_author)
#             # db.refresh(course_author)  # Refresh to get the latest state of the course
#         db.commit()

#         return {
#             "message": "Course created successfully",
#             "course": {
#                 "id": new_course.id,
#                 "title": new_course.title,
#                 "mode": new_course.mode.value,
#                 "creator_ids": payload.creator_ids,
#             },
#         }
#     except HTTPException:
#         raise  # Re-raise HTTPException if it's already one
#     except Exception as e:
#         # Log the error for debugging purposes
#         print(f"An error occurred: {e}")
#         db.rollback()  # Rollback in case of error
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="An error occurred while creating the course",
#         )


# # ─── Endpoint: Update Course Details ─────────────────────────────────────
# @router.put("/courses/{course_id}/details")
# def update_course_details(
#     course_id: int, payload: CourseDetailsUpdate, db: Session = Depends(get_db)
# ):
#     try:
#         course = db.query(Course).filter(Course.id == course_id).first()
#         if not course:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
#             )

#         course_details = (
#             db.query(CourseDetails).filter(CourseDetails.course_id == course_id).first()
#         )
#         if not course_details:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND, detail="Course details not found"
#             )

#         if payload.syllabus_summary is not None:
#             course_details.syllabus_summary = payload.syllabus_summary
#         if payload.syllabus_path is not None:
#             course_details.syllabus_path = payload.syllabus_path
#         if payload.venue is not None:
#             course_details.venue = payload.venue
#         if payload.start_date is not None:
#             course_details.start_date = payload.start_date
#         if payload.end_date is not None:
#             course_details.end_date = payload.end_date
#         if payload.start_time is not None:
#             course_details.start_time = payload.start_time
#         if payload.end_time is not None:
#             course_details.end_time = payload.end_time
#         if payload.duration_in_hours is not None:
#             course_details.duration_in_hours = payload.duration_in_hours

#         if payload.title is not None:
#             course.title = payload.title
#         if payload.description is not None:
#             course.description = payload.description

#         course_details.updated_at = datetime.utcnow()

#         db.commit()

#         return {
#             "message": "Course details updated successfully",
#             "course_details": {
#                 "course_id": course_details.course_id,
#                 "syllabus_summary": course_details.syllabus_summary,
#                 "syllabus_path": course_details.syllabus_path,
#                 "venue": course_details.venue,
#                 "start_date": course_details.start_date,
#                 "end_date": course_details.end_date,
#                 "start_time": course_details.start_time,
#                 "end_time": course_details.end_time,
#                 "duration_in_hours": course_details.duration_in_hours,
#                 "title": course.title,
#                 "description": course.description,
#             },
#         }
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"An error occurred: {e}")
#         db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="An error occurred while updating the course details",
#         )


# # ─── Endpoint: Get All Course Details ──────────────────────────────
# @router.get("/courses/details")
# def get_all_course_details(db: Session = Depends(get_db)):
#     try:
#         courses = db.query(Course).all()
#         result = []
#         for course in courses:
#             details = (
#                 db.query(CourseDetails)
#                 .filter(CourseDetails.course_id == course.id)
#                 .first()
#             )
#             if details:
#                 result.append(
#                     {
#                         "course_id": course.id,
#                         "title": course.title,
#                         "description": course.description,
#                         "mode": (
#                             course.mode.value
#                             if hasattr(course.mode, "value")
#                             else str(course.mode)
#                         ),
#                         "syllabus_summary": details.syllabus_summary,
#                         "syllabus_path": details.syllabus_path,
#                         "venue": details.venue,
#                         "start_date": details.start_date,
#                         "end_date": details.end_date,
#                         "start_time": details.start_time,
#                         "end_time": details.end_time,
#                         "duration_in_hours": details.duration_in_hours,
#                         "created_at": details.created_at,
#                         "updated_at": details.updated_at,
#                     }
#                 )
#         return {"courses": result}
#     except Exception as e:
#         print(f"An error occurred: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="An error occurred while fetching course details",
#         )


# # ─── Endpoint: Get Course Details By ID ──────────────────────────────
# @router.get("/courses/{course_id}/details")
# def get_course_details_by_id(course_id: int, db: Session = Depends(get_db)):
#     try:
#         course = db.query(Course).filter(Course.id == course_id).first()
#         if not course:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
#             )
#         details = (
#             db.query(CourseDetails).filter(CourseDetails.course_id == course.id).first()
#         )
#         if not details:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND, detail="Course details not found"
#             )
#         return {
#             "course_id": course.id,
#             "title": course.title,
#             "description": course.description,
#             "mode": (
#                 course.mode.value if hasattr(course.mode, "value") else str(course.mode)
#             ),
#             "syllabus_summary": details.syllabus_summary,
#             "syllabus_path": details.syllabus_path,
#             "venue": details.venue,
#             "start_date": details.start_date,
#             "end_date": details.end_date,
#             "start_time": details.start_time,
#             "end_time": details.end_time,
#             "duration_in_hours": details.duration_in_hours,
#             "created_at": details.created_at,
#             "updated_at": details.updated_at,
#         }
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"An error occurred: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="An error occurred while fetching course details",
#         )
