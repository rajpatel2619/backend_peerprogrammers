# app/routes/signup.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from . import auth
from datetime import datetime
from .login import login_user
from .login import LoginRequest
from ...connection.utility import get_db
from ...schemas.user_schema import *
from ...models.user_model import User, UserDetails, UserSocialDetails

router = APIRouter()
# app/schemas.py


@router.post("/signup")
def signup_user(signup_data: SignUpSchema, db: Session = Depends(get_db)):
    # These are the data inside signup_data
    # email, first_name, last_name, phone_number, password, repassword, accountType
    try:
        if signup_data.password != signup_data.repassword:
            raise HTTPException(status_code=400, detail="Passwords do not match")

        existing_user = db.query(User).filter(User.username == signup_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_password = auth.get_password_hash(signup_data.password)

        # Create user
        new_user = User(
            username=signup_data.email,
            password=hashed_password
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)



        # UserDetails
        userDetails = UserDetails(
            userId=new_user.id,
            firstName=signup_data.first_name,
            lastName=signup_data.last_name,
            phoneNumber=signup_data.phone_number,
            email=signup_data.email,
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow(),
            # isStudent=True if signup_data.accountType == "Student" else False
        )
        db.add(userDetails)

        # UserSocialDetails
        userSocial = UserSocialDetails(
            userId=new_user.id,
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        )
        db.add(userSocial)

        db.commit()
        return login_user(LoginRequest(email = signup_data.email, password = signup_data.password), db=db)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
