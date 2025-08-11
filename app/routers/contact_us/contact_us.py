from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from ...models.contact_us_model import ContactUs  # Our SQLAlchemy model
from ...connection.utility import get_db
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/contact_us", tags=["Contact Us"])

# -------------------------------
# Pydantic Schemas
# -------------------------------
class ContactUsCreate(BaseModel):
    name: str
    email: EmailStr
    inquiry_type: Optional[str] = "general"
    subject: str
    message: str

class ContactUsResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    inquiry_type: str
    subject: str
    message: str
    created_at: datetime

    class Config:
        orm_mode = True

class ContactUsUpdate(BaseModel):
    inquiry_type: Optional[str]
    subject: Optional[str]
    message: Optional[str]

# -------------------------------
# CREATE - Submit new inquiry
# -------------------------------
@router.post("/", response_model=ContactUsResponse)
def create_contact_us(contact: ContactUsCreate, db: Session = Depends(get_db)):
    new_contact = ContactUs(
        name=contact.name,
        email=contact.email,
        inquiry_type=contact.inquiry_type,
        subject=contact.subject,
        message=contact.message
    )
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    return new_contact

# -------------------------------
# READ - Get all inquiries (with optional filtering & pagination)
# -------------------------------
@router.get("/", response_model=List[ContactUsResponse])
def get_all_contacts(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20,
    inquiry_type: Optional[str] = None
):
    query = db.query(ContactUs)
    if inquiry_type:
        query = query.filter(ContactUs.inquiry_type == inquiry_type)
    contacts = query.order_by(ContactUs.created_at.desc()).offset(skip).limit(limit).all()
    return contacts

# -------------------------------
# READ - Get single inquiry by ID
# -------------------------------
@router.get("/{contact_id}", response_model=ContactUsResponse)
def get_contact_by_id(contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(ContactUs).filter(ContactUs.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact entry not found")
    return contact

# -------------------------------
# UPDATE - Update an inquiry
# -------------------------------
@router.put("/{contact_id}", response_model=ContactUsResponse)
def update_contact(contact_id: int, updates: ContactUsUpdate, db: Session = Depends(get_db)):
    contact = db.query(ContactUs).filter(ContactUs.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact entry not found")
    
    for key, value in updates.dict(exclude_unset=True).items():
        setattr(contact, key, value)

    db.commit()
    db.refresh(contact)
    return contact

# -------------------------------
# DELETE - Remove an inquiry
# -------------------------------
@router.delete("/{contact_id}")
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(ContactUs).filter(ContactUs.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact entry not found")
    
    db.delete(contact)
    db.commit()
    return {"message": f"Contact entry with ID {contact_id} deleted successfully"}
