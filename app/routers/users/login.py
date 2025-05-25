from . import auth
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...connection.utility import get_db
from ...schemas.user_schema import *
from ...models.user_model import *

router = APIRouter()


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