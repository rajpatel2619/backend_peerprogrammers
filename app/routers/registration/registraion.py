from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...models.course_model import *
from ...models.registration_model import *
from ...models.user_model import *
from ...connection.utility import get_db

router = APIRouter(prefix="/registrations", tags=["Registrations"])

# Register a user to a course
@router.post("/")
def register_user(
    user_id: int,
    course_id: int,
    transaction_id: str = None,
    fee: int = None,
    db: Session = Depends(get_db)
):
    existing = db.query(CourseRegistration).filter_by(
        user_id=user_id,
        course_id=course_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Already registered.")

    reg = CourseRegistration(
        user_id=user_id,
        course_id=course_id,
        transaction_id=transaction_id,
        payment_date = datetime.utcnow(),
        fee = fee
        
    )
    db.add(reg)
    db.commit()
    db.refresh(reg)
    return {
        "message": "Registered successfully",
        "registration_id": reg.id,
        "user_id": reg.user_id,
        "course_id": reg.course_id,
        "fee": reg.fee,
        "transaction_id": reg.transaction_id,
        "payment_date": reg.payment_date,
        "joined_at": reg.joined_at,
    }


@router.get("/count/{course_id}")
def get_registration_count(course_id: int, db: Session = Depends(get_db)):
    count = db.query(CourseRegistration).filter_by(course_id=course_id).count()
    return {
        "course_id": course_id,
        "registration_count": count
    }


@router.get("/user/{user_id}")
def get_registrations_by_user(user_id: int, db: Session = Depends(get_db)):
    regs = db.query(CourseRegistration).filter_by(user_id=user_id).all()
    return regs


@router.get("/{registration_id}")
def get_registration_by_id(registration_id: int, db: Session = Depends(get_db)):
    reg = db.query(CourseRegistration).get(registration_id)
    if not reg:
        raise HTTPException(status_code=404, detail="Registration not found")
    return reg


