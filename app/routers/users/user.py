from . import auth
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...connection.utility import get_db
from ...schemas.user_schema import *
from ...models.user_model import *
from datetime import datetime

router = APIRouter()

@router.get("/all_users")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()

    user_list = []
    for user in users:
        user_details = db.query(UserDetails).filter(UserDetails.userId == user.id).first()

        first_name = user_details.firstName if user_details else None
        last_name = user_details.lastName if user_details else None
        email = user_details.email if user_details else None
        full_name = f"{first_name} {last_name}".strip() if first_name or last_name else None

        user_list.append({
            "id": user.id,
            "username": user.username,
            "email": email,
            "name": full_name,
        })

    return {"users": user_list}


@router.get("/user_details/{user_id}")
def get_user_details(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_details = db.query(UserDetails).filter(UserDetails.userId == user.id).first()
    social_details = db.query(UserSocialDetails).filter(UserSocialDetails.userId == user.id).first()

    response = {
        "id": user.id,
        "username": user.username,
        "active": user.active,
        "createdAt": user.createdAt,
        "updatedAt": user.updatedAt,
        "details": {
            "firstName": user_details.firstName if user_details else None,
            "lastName": user_details.lastName if user_details else None,
            "phoneNumber": user_details.phoneNumber if user_details else None,
            "email": user_details.email if user_details else None,
            "address": user_details.address if user_details else None,
            "dob": user_details.dob if user_details else None,
        },
        "social": {
            "facebook": social_details.facebook if social_details else None,
            "github": social_details.github if social_details else None,
            "linkedin": social_details.linkedin if social_details else None,
            "medium": social_details.medium if social_details else None,
            "youtube": social_details.youtube if social_details else None,
            "twitter": social_details.twitter if social_details else None,
            "instagram": social_details.instagram if social_details else None,
            "personalWebsite": social_details.personalWebsite if social_details else None,
        },
    }

    return {"user": response}

@router.put("/update_user")
def update_user(payload: UserUpdateSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == payload.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.updatedAt = datetime.utcnow()

    # Update or create user details
    user_details = db.query(UserDetails).filter(UserDetails.userId == user.id).first()
    if not user_details:
        user_details = UserDetails(userId=user.id)
        db.add(user_details)

    user_details.firstName = payload.first_name
    user_details.lastName = payload.last_name
    user_details.phoneNumber = payload.phone_number
    user_details.address = payload.address
    user_details.dob = payload.dob

    # Update or create social details
    social_details = db.query(UserSocialDetails).filter(UserSocialDetails.userId == user.id).first()
    if not social_details:
        social_details = UserSocialDetails(userId=user.id)
        db.add(social_details)

    social_details.facebook = payload.facebook
    social_details.github = payload.github
    social_details.linkedin = payload.linkedin
    social_details.medium = payload.medium
    social_details.youtube = payload.youtube
    social_details.twitter = payload.twitter
    social_details.instagram = payload.instagram
    social_details.personalWebsite = payload.personal_website

    db.commit()

    updated_user = {
        "id": user.id,
        "username": user.username,
        "active": user.active,
        "createdAt": user.createdAt,
        "updatedAt": user.updatedAt,
        "details": {
            "firstName": user_details.firstName,
            "lastName": user_details.lastName,
            "phoneNumber": user_details.phoneNumber,
            "email": user_details.email,
            "address": user_details.address,
            "dob": user_details.dob,
        },
        "social": {
            "facebook": social_details.facebook,
            "github": social_details.github,
            "linkedin": social_details.linkedin,
            "medium": social_details.medium,
            "youtube": social_details.youtube,
            "twitter": social_details.twitter,
            "instagram": social_details.instagram,
            "personalWebsite": social_details.personalWebsite,
        },
    }

    return {"message": "User updated successfully", "user": updated_user}
