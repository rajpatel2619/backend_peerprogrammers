# app/routes/signup.py

from email.message import EmailMessage
import random
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from . import auth
from datetime import datetime, timedelta
from .login import login_user
from .login import LoginRequest
from ...connection.utility import get_db
from ...schemas.user_schema import *
from ...models.user_model import *
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

router = APIRouter()
# app/schemas.py



def send_otp(receiver_email, sender_email, sender_password, otp):

    # msg = EmailMessage()
    # msg['subject'] = 'OTP Verification'
    # msg['from'] = sender_email
    # msg['to'] = receiver_email
    # msg.set_content(f"Your OTP is: {otp}\nThis OTP is valid for 5 minutes.")

    # try:
    #     with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
    #         smtp.login(sender_email, sender_password)
    #         smtp.send_message(msg)
    #     print("OTP sent successfully!")

    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"Failed to send OTP: {str(e)}")
    
    message = MIMEMultipart("alternative")
    message["Subject"] = "🔐 OTP Verification"
    message["From"] = sender_email
    message["To"] = receiver_email

    # Manual Templates
    plain_text = f"""
Hello,

Your One-Time Password (OTP) is: {otp}

This OTP is valid for 5 minutes.

Thank you,
Your Company Name
"""

    html_text = f"""
<html>
  <body>
    <h2>🔐 OTP Verification</h2>
    <p>Your <strong>One-Time Password (OTP)</strong> is:</p>
    <h3 style="color:blue;">{otp}</h3>
    <p>This OTP is valid for 5 minutes.</p>
    <br>
    <p>Thank you,<br>Your Company Name</p>
  </body>
</html>
"""

    message.attach(MIMEText(plain_text, "plain"))
    message.attach(MIMEText(html_text, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())


@router.post("/temp-signup")
def temp_signup_user(signup_data: dict, db: Session = Depends(get_db)):
    try:
        email = signup_data.get("email")
        first_name = signup_data.get("first_name")
        last_name = signup_data.get("last_name")
        phone_number = signup_data.get("phone_number")
        password = signup_data.get("password")
        repassword = signup_data.get("repassword")
        preferred_account = signup_data.get("accountType")

        if not all([email, first_name, last_name, phone_number, password, repassword, preferred_account]):
            raise HTTPException(status_code=400, detail="All fields are required")

        if password != repassword:
            raise HTTPException(status_code=400, detail="Passwords do not match")

        # Check if email already exists in users table
        existing_perm_user = db.query(User).filter(User.username == email).first()
        if existing_perm_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Remove existing temp user if exists
        existing_temp_user = db.query(TempUser).filter(TempUser.email == email).first()
        if existing_temp_user:
            db.delete(existing_temp_user)
            db.commit()

        # Generate OTP
        otp_code = ''.join(random.choices('0123456789', k=6))
        expires_at = datetime.utcnow() + timedelta(minutes=10)

        # Create TempUser
        new_temp_user = TempUser(
            email=email,
            password=password,  # Store plain password temporarily
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            otp=otp_code,
            preferredAccount=preferred_account,
            expires_at=expires_at
        )

        db.add(new_temp_user)
        db.commit()
        db.refresh(new_temp_user)

        # print(f"Generated OTP for {email}: {otp_code}")

        sender_email = "validations.peerprogrammers@gmail.com"
        sender_password = "zhiuhrdnosuxqarf"
        send_otp(email, sender_email, sender_password, otp_code)


        return {
            "message": "Temporary user created successfully. Please verify your email using the OTP.",
            "userId": new_temp_user.id,
            "user": {
                "email": new_temp_user.email,
                "first_name": new_temp_user.first_name,
                "last_name": new_temp_user.last_name,
                "phone_number": new_temp_user.phone_number,
                "otp": new_temp_user.otp
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f" {e}")


@router.post("/verify-otp")
def verify_otp(data: dict, db: Session = Depends(get_db)):
    try:
        email = data.get("email")
        otp_code = data.get("otp")

        if not email or not otp_code:
            raise HTTPException(status_code=400, detail="Email and OTP are required")

        temp_user = db.query(TempUser).filter(TempUser.email == email).first()

        if not temp_user:
            raise HTTPException(status_code=404, detail="Temporary user not found")

        if temp_user.otp != otp_code:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        if datetime.utcnow() > temp_user.expires_at:
            raise HTTPException(status_code=400, detail="OTP has expired")

        # Check if email is already registered in users
        existing_user = db.query(User).filter(User.username == email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create User (Account Info)
        new_user = User(
            username=temp_user.email,
            password=auth.get_password_hash(temp_user.password),
            preferredAccount=temp_user.preferredAccount,
            active=True,
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Create UserDetails (Personal Info)
        user_details = UserDetails(
            userId=new_user.id,
            firstName=temp_user.first_name,
            lastName=temp_user.last_name,
            phoneNumber=temp_user.phone_number,
            email=temp_user.email,
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        )
        db.add(user_details)

        # Create UserSocialDetails (Empty by default)
        user_social = UserSocialDetails(
            userId=new_user.id,
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        )
        db.add(user_social)

        db.commit()

        # Remove TempUser after successful transfer
        db.delete(temp_user)
        db.commit()

        return {
            "message": "OTP verified successfully. User created.",
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "preferredAccount": new_user.preferredAccount,
                "active": new_user.active,
                "createdAt": new_user.createdAt,
                "updatedAt": new_user.updatedAt
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(e)
        raise HTTPException(status_code=500, detail=f" {e}")



@router.post("/forget-password")
def forget_password(data: dict, db: Session = Depends(get_db)):
    try:
        email = data.get("email")

        if not email:
            raise HTTPException(status_code=400, detail="Email is required")

        # Check if user exists in users table
        user = db.query(User).filter(User.username == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Remove existing forget password entry if exists
        existing_fp = db.query(ForgetPassword).filter(ForgetPassword.email == email).first()
        if existing_fp:
            db.delete(existing_fp)
            db.commit()

        # Generate OTP
        otp_code = ''.join(random.choices('0123456789', k=6))
        expires_at = datetime.utcnow() + timedelta(minutes=10)

        # Save OTP in forget_password table
        forget_password_entry = ForgetPassword(
            email=email,
            otp=otp_code,
            expiredAt=expires_at
        )

        db.add(forget_password_entry)
        db.commit()

        sender_email = "validations.peerprogrammers@gmail.com"
        sender_password = "zhiuhrdnosuxqarf"
        send_otp(email, sender_email, sender_password, otp_code)


        # In real app, send OTP via email or SMS
        # print(f"Generated OTP for {email}: {otp_code}")

        return {
            "message": "OTP generated successfully. Please check your email.",
            "email": email
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f" {e}")

@router.post("/verify-forget-password")
def verify_forget_password(data: dict, db: Session = Depends(get_db)):
    try:
        email = data.get("email")
        otp_code = data.get("otp")
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")

        if not all([email, otp_code, new_password, confirm_password]):
            raise HTTPException(status_code=400, detail="Email, OTP, new password, and confirm password are required")

        # Fetch record from forget_password table
        forget_entry = db.query(ForgetPassword).filter(ForgetPassword.email == email).first()

        if not forget_entry:
            raise HTTPException(status_code=404, detail="OTP not found for this email")

        if forget_entry.otp != otp_code: 
            raise HTTPException(status_code=400, detail="Invalid OTP")

        if datetime.utcnow() > forget_entry.expiredAt:
            raise HTTPException(status_code=400, detail="OTP has expired")

        # Delete OTP entry
        db.delete(forget_entry)
        db.commit()

        # Internally reset password
        user = db.query(User).filter(User.username == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if new_password != confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")

        hashed_password = auth.get_password_hash(new_password)
        user.password = hashed_password
        user.updatedAt = datetime.utcnow()

        db.commit()

        return {
            "message": "OTP verified and password reset successfully.",
            "email": email
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f" {e}")
