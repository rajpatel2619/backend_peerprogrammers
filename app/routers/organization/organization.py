from fastapi import APIRouter, Depends, HTTPException, Form
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
from ...models.organization_model import Organization
from ...connection.utility import get_db

router = APIRouter(prefix="/organizations", tags=["Organizations"])

# ===============================
# CREATE ORGANIZATION
# ===============================
@router.post("/create")
def create_organization(
    name: str = Form(...),
    poc_name: str = Form(...),
    poc_contact_number: str = Form(...),
    poc_email: str = Form(...),
    address: str = Form(...),
    message: Optional[str] = Form(None),
    expected_participants: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    org = Organization(name=name, poc_name=poc_name, poc_contact_number=poc_contact_number,
                       poc_email=poc_email, address=address, message=message,
                       expected_participants=expected_participants, created_at=datetime.utcnow())
    db.add(org)
    db.commit()
    db.refresh(org)
    return {"message": "Organization created", "organization_id": org.id}


# ===============================
# GET ALL ORGANIZATIONS
# ===============================
@router.get("/all")
def get_all_organizations(db: Session = Depends(get_db)):
    orgs = db.query(Organization).filter(Organization.deleted == False).all()
    return [
        {
            "id": o.id,
            "name": o.name,
            "poc_name": o.poc_name,
            "poc_contact_number": o.poc_contact_number,
            "poc_email": o.poc_email,
            "address": o.address,
            "message": o.message,
            "expected_participants": o.expected_participants,
            "created_at": o.created_at,
            "updated_at": o.updated_at
        }
        for o in orgs
    ]


# ===============================
# GET ORGANIZATION BY ID
# ===============================
@router.get("/{organization_id}")
def get_organization_by_id(organization_id: int, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == organization_id, Organization.deleted == False).first()
    if not org:
        raise HTTPException(404, "Organization not found")
    return {
        "id": org.id,
        "name": org.name,
        "poc_name": org.poc_name,
        "poc_contact_number": org.poc_contact_number,
        "poc_email": org.poc_email,
        "address": org.address,
        "message": org.message,
        "expected_participants": org.expected_participants,
        "created_at": org.created_at,
        "updated_at": org.updated_at
    }


# ===============================
# UPDATE ORGANIZATION
# ===============================
@router.put("/update/{organization_id}")
def update_organization(
    organization_id: int,
    name: Optional[str] = Form(None),
    poc_name: Optional[str] = Form(None),
    poc_contact_number: Optional[str] = Form(None),
    poc_email: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    message: Optional[str] = Form(None),
    expected_participants: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    org = db.query(Organization).filter(Organization.id == organization_id, Organization.deleted == False).first()
    if not org:
        raise HTTPException(404, "Organization not found")

    if name:
        org.name = name
    if poc_name:
        org.poc_name = poc_name
    if poc_contact_number:
        org.poc_contact_number = poc_contact_number
    if poc_email:
        org.poc_email = poc_email
    if address:
        org.address = address
    if message is not None:
        org.message = message
    if expected_participants is not None:
        org.expected_participants = expected_participants

    org.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(org)
    return {"message": "Organization updated", "organization_id": org.id}


# ===============================
# DELETE ORGANIZATION
# ===============================
@router.delete("/delete/{organization_id}")
def delete_organization(organization_id: int, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == organization_id, Organization.deleted == False).first()
    if not org:
        raise HTTPException(404, "Organization not found")

    org.deleted = True
    org.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Organization deleted", "organization_id": org.id}
