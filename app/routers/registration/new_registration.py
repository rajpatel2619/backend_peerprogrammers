from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import razorpay
import os
from dotenv import load_dotenv
from ...connection.utility import get_db
from ...models.new_registration_model import CustomerPayment
from ...models.course_model import Courses
from typing import Optional

# Load environment variables
load_dotenv()

# Razorpay client setup
razorpay_client = razorpay.Client(
    auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET"))
)

router = APIRouter(prefix="/buy", tags=["Buy"])


from pydantic import BaseModel

class OrderRequest(BaseModel):
    name: str
    number: str
    email: str
    amount: int
    course_id: int


@router.post("/create-order-id")
def create_order_id(order: OrderRequest, db: Session = Depends(get_db)):
    try:
        course = db.query(Courses).filter_by(id=order.course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        order_data = razorpay_client.order.create(dict(
            amount=order.amount * 100,
            currency="INR",
            receipt=f"order_{order.course_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            payment_capture=1
        ))

        new_payment = CustomerPayment(
            name=order.name,
            number=order.number,
            email=order.email,
            course_id=order.course_id,
            amount=order.amount,
            currency="INR",
            status="created",
            razorpay_order_id=order_data["id"],
            payment_date=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(new_payment)
        db.commit()
        db.refresh(new_payment)

        return {
            "message": "Order ID created successfully",
            "order_id": order_data["id"],
            "amount": order_data["amount"],
            "currency": order_data["currency"],
            "user_details": order.dict(),
            "payment_record_id": new_payment.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from pydantic import BaseModel

class VerifyPaymentRequest(BaseModel):
    payment_id: int
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str
    payment_method: str = ""

@router.post("/verify-payment")
def verify_payment(payload: VerifyPaymentRequest, db: Session = Depends(get_db)):
    try:
        payment_record = db.query(CustomerPayment).filter_by(id=payload.payment_id).first()
        if not payment_record:
            raise HTTPException(status_code=404, detail="Payment record not found")

        razorpay_client.utility.verify_payment_signature({
            'razorpay_order_id': payload.razorpay_order_id,
            'razorpay_payment_id': payload.razorpay_payment_id,
            'razorpay_signature': payload.razorpay_signature
        })

        payment_record.razorpay_payment_id = payload.razorpay_payment_id
        payment_record.razorpay_signature = payload.razorpay_signature
        payment_record.payment_method = payload.payment_method
        payment_record.status = "captured"
        payment_record.payment_date = datetime.utcnow()
        payment_record.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(payment_record)

        return {
            "message": "Payment verified successfully",
            "payment_id": payment_record.id,
            "order_id": payload.razorpay_order_id,
            "status": payment_record.status
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payments")
def get_all_payments(db: Session = Depends(get_db)):
    payments = db.query(CustomerPayment).all()
    return payments


@router.get("/payments/{payment_id}")
def get_payment_by_id(payment_id: int, db: Session = Depends(get_db)):
    payment = db.query(CustomerPayment).filter_by(id=payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.get("/payments/by-course/{course_id}")
def get_payments_by_course(course_id: int, db: Session = Depends(get_db)):
    payments = db.query(CustomerPayment).filter_by(course_id=course_id).all()
    if not payments:
        raise HTTPException(status_code=404, detail="No payments found for this course")
    return payments


@router.get("/courses")
def get_all_courses(db: Session = Depends(get_db)):
    courses = db.query(Courses).all()
    return courses


@router.get("/courses/{course_id}")
def get_course_by_id(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Courses).filter_by(id=course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course
