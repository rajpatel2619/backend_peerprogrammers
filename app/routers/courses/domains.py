import os
import shutil
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from pathlib import Path

from ...connection.utility import get_db
from ...schemas.course_schema import *
from ...models.course_model import *
from ...models.user_model import *



router = APIRouter(tags=['Domains'])




# DOMAINS RELATED APIS

@router.post("/domain_tags/create")
def create_domain_tag(payload: dict, db: Session = Depends(get_db)):
    name = payload.get("name")
    created_by = payload.get("createdBy")

    if not name or not created_by:
        raise HTTPException(status_code=400, detail="Both 'name' and 'createdBy' are required")

    existing = db.query(DomainTag).filter(DomainTag.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Domain tag already exists")

    new_tag = DomainTag(name=name, createdBy=created_by)
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)

    return {
        "success": True,
        "message": "Domain tag created successfully",
        "tag_id": new_tag.id,
        "tag_name": new_tag.name
    }



@router.put("/domain-tags/update/{tag_id}")
def update_domain_tag(tag_id: int, payload: dict, db: Session = Depends(get_db)):
    tag = db.query(DomainTag).filter(DomainTag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Domain tag not found")

    new_name = payload.get("name")
    if not new_name:
        raise HTTPException(status_code=400, detail="'name' is required to update")

    tag.name = new_name
    db.commit()
    db.refresh(tag)

    return {
        "success": True,
        "message": "Domain tag updated successfully",
        "tag_id": tag.id,
        "new_name": tag.name
    }



@router.put("/domain-tags/verify/{tag_id}")
def verify_domain_tag(tag_id: int, payload: dict, db: Session = Depends(get_db)):
    tag = db.query(DomainTag).filter(DomainTag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Domain tag not found")


    if tag.isVerified:
        return {"success": True, "message": "Domain tag already verified", "tag_id": tag.id}

    tag.isVerified = True
    db.commit()
    db.refresh(tag)

    return {
        "success": True,
        "message": "Domain tag verified successfully",
        "tag_id": tag.id,
    }



@router.get("/domain-tags/verified")
def get_verified_domain_tags(db: Session = Depends(get_db)):
    tags = db.query(DomainTag).filter(DomainTag.isVerified == True).order_by(DomainTag.name).all()

    return {
        "success": True,
        "total": len(tags),
        "tags": [
            {
                "id": tag.id,
                "name": tag.name,
                "createdBy": tag.createdBy,
            }
            for tag in tags
        ]
    }


@router.get("/domain-tags/unverified")
def get_unverified_domain_tags(db: Session = Depends(get_db)):
    tags = db.query(DomainTag).filter(DomainTag.isVerified == False).order_by(DomainTag.name).all()

    return {
        "success": True,
        "total": len(tags),
        "tags": [
            {
                "id": tag.id,
                "name": tag.name,
                "createdBy": tag.createdBy,
            }
            for tag in tags
        ]
    }


