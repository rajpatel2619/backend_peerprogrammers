from . import auth
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...connection.utility import get_db
from ...schemas.user_schema import *
from ...models.user_model import *

router = APIRouter()

@router.post("/login")
def login_user(payload: dict, db: Session = Depends(get_db)):
    try:
        email = payload.get("email")
        password = payload.get("password")

        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and Password are required")

        user = db.query(User).filter(User.username == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not auth.verify_password(password, user.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Fetch user details and social details
        user_details = db.query(UserDetails).filter(UserDetails.userId == user.id).first()
        social_details = db.query(UserSocialDetails).filter(UserSocialDetails.userId == user.id).first()

        token = auth.create_access_token(data={"sub": user.username})

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "active": user.active,
                "createdAt": user.createdAt,
                "updatedAt": user.updatedAt,
                "preferredAccount": user.preferredAccount,
                "userType": user.userType,
                "details": {
                    "firstName": user_details.firstName if user_details else None,
                    "lastName": user_details.lastName if user_details else None,
                    "phoneNumber": user_details.phoneNumber if user_details else None,
                    "email": user_details.email if user_details else None,
                    "address": user_details.address if user_details else None,
                    "dob": user_details.dob if user_details else None,
                } if user_details else None,
                "social": {
                    "facebook": social_details.facebook if social_details else None,
                    "github": social_details.github if social_details else None,
                    "linkedin": social_details.linkedin if social_details else None,
                    "medium": social_details.medium if social_details else None,
                    "youtube": social_details.youtube if social_details else None,
                    "twitter": social_details.twitter if social_details else None,
                    "instagram": social_details.instagram if social_details else None,
                    "personalWebsite": social_details.personalWebsite if social_details else None,
                } if social_details else None,
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
