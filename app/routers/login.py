from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import SessionLocal, Base, engine
from sqlalchemy import Column, Integer, String
from .. import crud, schemas, auth
from ..models import TestUser, User, UserDetails, UserSocialDetails
from pydantic import BaseModel

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
def login_user(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email
    password = payload.password
    user = db.query(User).filter(User.username == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not auth.verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer", "user": user}