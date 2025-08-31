from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import razorpay
import os
from dotenv import load_dotenv
from ...connection.utility import get_db
from ...models.new_registration_model import CustomerPayment
from ...models.course_model import Courses

# Load environment variables
load_dotenv()

# Razorpay client setup
razorpay_client = razorpay.Client(
    auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET"))
)

router = APIRouter(prefix="/buy", tags=["Buy"])

@router.post("/create-order-id")
def create_order_id(
    name: str,
    number: str,
    email: str,
    age: int,
    amount: int,      # in rupees
    course_id: int,   # course ID
    db: Session = Depends(get_db)
):
    try:
        # Check if course exists
        course = db.query(Courses).filter_by(id=course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        # Create Razorpay order
        order = razorpay_client.order.create(dict(
            amount=amount * 100,  # Convert to paise
            currency="INR",
            receipt=f"order_{course_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            payment_capture=1
        ))

        # Store user and payment details in database
        new_payment = CustomerPayment(
            name=name,
            number=number,
            email=email,
            age=age,
            course_id=course_id,
            amount=amount,
            currency="INR",
            status="created",
            razorpay_order_id=order["id"],
            payment_date=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(new_payment)
        db.commit()
        db.refresh(new_payment)

        return {
            "message": "Order ID created successfully",
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "user_details": {
                "name": name,
                "number": number,
                "email": email,
                "age": age
            },
            "course_id": course_id,
            "payment_record_id": new_payment.id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/verify-payment")
def verify_payment(
    payment_id: int,
    razorpay_payment_id: str,
    razorpay_order_id: str,
    razorpay_signature: str,
    payment_method: str = "",
    db: Session = Depends(get_db)
):
    try:
        # Fetch payment record
        payment_record = db.query(CustomerPayment).filter_by(id=payment_id).first()
        if not payment_record:
            raise HTTPException(status_code=404, detail="Payment record not found")

        # Verify Razorpay signature
        try:
            razorpay_client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })
        except:
            raise HTTPException(status_code=400, detail="Payment verification failed")

        # Update payment record after successful verification
        payment_record.razorpay_payment_id = razorpay_payment_id
        payment_record.razorpay_signature = razorpay_signature
        payment_record.payment_method = payment_method
        payment_record.status = "captured"
        payment_record.payment_date = datetime.utcnow()
        payment_record.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(payment_record)

        return {
            "message": "Payment verified successfully",
            "payment_id": payment_record.id,
            "order_id": razorpay_order_id,
            "status": payment_record.status
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))