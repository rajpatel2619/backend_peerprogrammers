from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...models.course_model import *
from ...models.registration_model import *
from ...models.user_model import *
from ...connection.utility import get_db

router = APIRouter(prefix="/registrations", tags=["Registrations"])


# Register a user to a course
@router.post("/")
def register_user(user_id: int, course_id: int, payment_mode: str = None, db: Session = Depends(get_db)):
    existing = db.query(CourseRegistration).filter_by(
        user_id=user_id,
        course_id=course_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Already registered.")

    reg = CourseRegistration(
        user_id=user_id,
        course_id=course_id,
        payment_mode=payment_mode,
        has_paid=True
    )
    db.add(reg)
    db.commit()
    db.refresh(reg)
    return {
        "message": "Registered successfully",
        "registration_id": reg.id,
        "user_id": reg.user_id,
        "course_id": reg.course_id,
    }


# Get all registrations for a specific course
@router.get("/course/{course_id}")
def get_course_registrations(course_id: int, db: Session = Depends(get_db)):
    regs = db.query(CourseRegistration).filter_by(course_id=course_id).all()
    return [
        {
            "registration_id": r.id,
            "user_id": r.user_id,
            "has_paid": r.has_paid,
            "is_verified": r.is_verified,
            "joined_at": r.joined_at,
        } for r in regs
    ]


# Get all registrations for a specific user
@router.get("/user/{user_id}")
def get_user_registrations(user_id: int, db: Session = Depends(get_db)):
    regs = db.query(CourseRegistration).filter_by(user_id=user_id).all()
    return [
        {
            "registration_id": r.id,
            "course_id": r.course_id,
            "has_paid": r.has_paid,
            "is_verified": r.is_verified,
            "joined_at": r.joined_at,
        } for r in regs
    ]


# Verify a registration
@router.put("/{registration_id}/verify")
def verify_registration(registration_id: int, db: Session = Depends(get_db)):
    reg = db.query(CourseRegistration).filter_by(id=registration_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Registration not found.")
    
    reg.is_verified = True
    db.commit()
    return {"message": "Registration verified", "registration_id": reg.id}
