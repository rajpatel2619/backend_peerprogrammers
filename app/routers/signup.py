from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import inspect, Column, Integer, String
from ..database import engine, SessionLocal, Base
from .. import auth

from ..models import TestUser

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
    password: str,
    repassword: str,
    db: Session = Depends(get_db)
):
    try:
        if password != repassword:
            return {"error": "Passwords do not match"}

        inspector = inspect(engine)
        if not inspector.has_table("test_user"):
            TestUser.__table__.create(bind=engine)

        existing_user = db.query(TestUser).filter(TestUser.email == email).first()
        if existing_user:
            return {"error": "Email already registered"}

        hashed_password = auth.get_password_hash(password)
        
        db_user = TestUser(
            email=email,
            first_name=first_name,
            last_name=last_name,
            hashed_password=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return {"message": "User created successfully"}

    except Exception as e:
        return {"error": f"Internal Server Error: {e}"}

@router.delete("/drop-test-user-table")
def drop_test_user_table():
    try:
        TestUser.__table__.drop(bind=engine)
        return {"message": "test_user table dropped successfully"}
    except Exception as e:
        return {"error": f"Failed to drop test_user table: {e}"}
