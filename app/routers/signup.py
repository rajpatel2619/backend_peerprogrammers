from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import inspect, Column, Integer, String
from ..database import engine, SessionLocal, Base
from .. import auth
from ..models import User, UserDetails, UserSocialDetails

from ..models import TestUser
from datetime import datetime
from .login import login_user

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@router.post("/signup")
def signup_user(
    email: str,
    first_name: str,
    last_name: str,
    phone_number: str,
    password: str,
    repassword: str,
    db: Session = Depends(get_db)
):
    try:
        if password != repassword:
            return {"error": "Passwords do not match"}

        existing_user = db.query(User).filter(User.username == email).first()
        if existing_user:
            return {"error": "Email already registered"}

        hashed_password = auth.get_password_hash(password)

        # Create user entry
        new_user = User(
            username=email,
            password=hashed_password
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Create user details entry
        userDetails = UserDetails(
            userId=new_user.id,
            firstName=first_name,
            lastName=last_name,
            phoneNumber=phone_number,
            email=email,
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        )
        db.add(userDetails)

        userSocial = UserSocialDetails(
            userId=new_user.id,
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        )
        db.add(userSocial)


        db.commit()
        return login_user(email=email, password=password, db=db)
        return {"message": "User created successfully", "user": new_user}

    except Exception as e:
        db.rollback()
        return {"error": f"Internal Server Error: {e}"}


@router.delete("/drop-test-user-table")
def drop_test_user_table():
    try:
        TestUser.__table__.drop(bind=engine)
        return {"message": "test_user table dropped successfully"}
    except Exception as e:
        return {"error": f"Failed to drop test_user table: {e}"}
