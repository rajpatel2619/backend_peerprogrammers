from . import auth
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...connection.utility import get_db
from ...schemas.user_schema import *
from ...models.user_model import *
from sqlalchemy.orm import joinedload

router = APIRouter()


@router.post("/login")
def login_user(payload: dict, db: Session = Depends(get_db)):
    try:
        email = payload.get("email")
        password = payload.get("password")

        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and Password are required")

        # Load all related data in one go
        user = (
            db.query(User)
            .options(
                joinedload(User.user_details),
                joinedload(User.user_social_details)
            )
            .filter(User.username == email)
            .first()
        )

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not auth.verify_password(password, user.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = auth.create_access_token(data={"sub": user.username})

        # Build full response
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
                    "firstName": user.user_details.firstName if user.user_details else None,
                    "lastName": user.user_details.lastName if user.user_details else None,
                    "phoneNumber": user.user_details.phoneNumber if user.user_details else None,
                    "email": user.user_details.email if user.user_details else None,
                    "address": user.user_details.address if user.user_details else None,
                    "dob": user.user_details.dob if user.user_details else None,
                } if user.user_details else None,
                "social": {
                    "facebook": user.user_social_details.facebook if user.user_social_details else None,
                    "github": user.user_social_details.github if user.user_social_details else None,
                    "linkedin": user.user_social_details.linkedin if user.user_social_details else None,
                    "medium": user.user_social_details.medium if user.user_social_details else None,
                    "youtube": user.user_social_details.youtube if user.user_social_details else None,
                    "twitter": user.user_social_details.twitter if user.user_social_details else None,
                    "instagram": user.user_social_details.instagram if user.user_social_details else None,
                    "personalWebsite": user.user_social_details.personalWebsite if user.user_social_details else None,
                }

            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))