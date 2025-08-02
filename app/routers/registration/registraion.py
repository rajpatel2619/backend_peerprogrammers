from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime
import razorpay
import os
from dotenv import load_dotenv
from ...models.course_model import *
from ...models.registration_model import *
from ...models.user_model import *
from ...connection.utility import get_db

# Load environment variables
load_dotenv()

# Razorpay client setup
razorpay_client = razorpay.Client(
    auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET"))
)

router = APIRouter(prefix="/registrations", tags=["Registrations"])


# ─── 1. Create Razorpay Order ───────────────────────────────────────────────────
@router.post("/create-order")
def create_payment_order(
    user_id: int,
    course_id: int,
    amount: int,  # in rupees
    db: Session = Depends(get_db)
):
    # Check if already registered
    existing = db.query(CourseRegistration).filter_by(
        user_id=user_id, course_id=course_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already registered.")

    try:
        order = razorpay_client.order.create(dict(
            amount=amount * 100,  # convert to paise
            currency="INR",
            receipt=f"receipt_{user_id}_{course_id}",
            payment_capture=1
        ))
        return {
            "order":order,
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "user_id": user_id,
            "course_id": course_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── 2. Verify Razorpay Payment and Register ─────────────────────────────────────
@router.post("/verify")
def verify_and_register(
    user_id: int,
    course_id: int,
    transaction_id: str,
    order_id: str,
    signature: str,
    fee: int,
    email: str = "",
    contact: str = "",
    payment_method: str = "",
    db: Session = Depends(get_db)
):
    # 1. Verify Razorpay signature
    try:
        razorpay_client.utility.verify_payment_signature({
            'razorpay_order_id': order_id,
            'razorpay_payment_id': transaction_id,
            'razorpay_signature': signature
        })
    except:
        raise HTTPException(status_code=400, detail="Payment verification failed")

    # 2. Check duplicate registration
    existing = db.query(CourseRegistration).filter_by(
        user_id=user_id, course_id=course_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already registered.")

    # 3. Register user in CourseRegistration
    reg = CourseRegistration(
        user_id=user_id,
        course_id=course_id,
        transaction_id=transaction_id,
        payment_date=datetime.utcnow(),
        fee=fee
    )
    db.add(reg)
    db.commit()
    db.refresh(reg)

    # 4. Add entry in Payment table
    payment = Payment(
        registration_id=reg.id,
        amount=fee,
        currency="INR",
        status="captured",  # or fetch from Razorpay if needed
        razorpay_payment_id=transaction_id,
        razorpay_order_id=order_id,
        razorpay_signature=signature,
        payment_method=payment_method,
        email=email,
        contact=contact,
        payment_date=datetime.utcnow()
    )
    db.add(payment)
    db.commit()

    return {
        "message": "Payment verified and user registered",
        "registration_id": reg.id,
        "payment_id": payment.id
    }



# ─── 3. Get Registration Count ───────────────────────────────────────────────────
@router.get("/count/{course_id}")
def get_registration_count(course_id: int, db: Session = Depends(get_db)):
    count = db.query(CourseRegistration).filter_by(course_id=course_id).count()
    return {
        "course_id": course_id,
        "registration_count": count
    }


# ─── 4. Get User Registrations ───────────────────────────────────────────────────
@router.get("/user/{user_id}")
def get_registrations_by_user(user_id: int, db: Session = Depends(get_db)):
    regs = db.query(CourseRegistration).filter_by(user_id=user_id).all()
    return regs




# ─── 6. Check if User relation with Course ─────────────────────────────────
@router.get("/role-in-course/")
def get_user_role_in_course(user_id: int, course_id: int, db: Session = Depends(get_db)):
    # 1. Check if the course exists
    course = db.query(Courses).filter_by(id=course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # 2. Role priority: creator > mentor > student
    if course.creatorid == user_id:
        role = "creator"
    elif db.query(CourseMentor).filter_by(user_id=user_id, course_id=course_id).first():
        role = "mentor"
    elif db.query(CourseRegistration).filter_by(user_id=user_id, course_id=course_id).first():
        role = "student"
    else:
        role = "none"

    return {
        "role": role
    }



# ─── 7. Get Detailed Registered Courses of a User ─────────────────────────────
@router.get("/user/{user_id}/courses")
def get_registered_courses_detail(user_id: int, db: Session = Depends(get_db)):
    registrations = (
        db.query(CourseRegistration)
        .filter_by(user_id=user_id)
        .join(Courses, CourseRegistration.course_id == Courses.id)
        .all()
    )

    course_details = []
    for reg in registrations:
        course = db.query(Courses).filter_by(id=reg.course_id).first()
        if course:
            course_details.append({
                "course_id": course.id,
                "title": course.title,
                "description": course.description,
                "mode": course.mode,
                "start_date": course.start_date,
                "price": course.price,
                "creator_id": course.creatorid,
                "registered_on": reg.payment_date,
            })

    return {
        "user_id": user_id,
        "registered_courses": course_details
    }
