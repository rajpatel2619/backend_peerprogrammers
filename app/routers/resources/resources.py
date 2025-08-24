from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from ...connection.utility import get_db
from ...models.resource_model import Domain, Subdomain, Resource, ResourceVote
from ...models.user_model import User   # assuming you already have this

router = APIRouter(prefix="/resources", tags=["Resources"])


@router.get("/unverified")
def get_unverified_resources(db: Session = Depends(get_db)):
    try:
        resources = db.query(Resource).filter_by(is_verified=False).all()
        return [
            {
                "id": r.id,
                "title": r.title,
                "description": r.description,
                "link": r.link,
                "upvote": r.upvote,
                "downvote": r.downvote,
                "domain_id": r.domain_id,
                "subdomain_id": r.subdomain_id,
                "added_by_id": r.added_by_id,
                "is_verified": r.is_verified
            } for r in resources
        ]
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/{resource_id}/verify")
def verify_resource(resource_id: int, db: Session = Depends(get_db)):
    try:
        resource = db.query(Resource).filter_by(id=resource_id).first()
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        if resource.is_verified:
            return {"message": "Resource is already verified"}

        resource.is_verified = True
        db.commit()
        db.refresh(resource)
        return {"message": "Resource verified successfully", "resource_id": resource.id}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")



# ✅ Create a new resource using IDs
@router.post("/upload-resource")
def create_resource(payload: dict, db: Session = Depends(get_db)):
    try:
        title = payload.get("title")
        description = payload.get("description")
        link = payload.get("link")
        domain_id = payload.get("domain_id")
        subdomain_id = payload.get("subdomain_id")
        added_by_id = payload.get("added_by_id")

        if not all([title, link, domain_id, subdomain_id, added_by_id]):
            raise HTTPException(status_code=400, detail="Missing required fields")

        # Validate IDs
        domain = db.query(Domain).filter_by(id=domain_id).first()
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")

        subdomain = db.query(Subdomain).filter_by(id=subdomain_id, domain_id=domain_id).first()
        if not subdomain:
            raise HTTPException(status_code=404, detail="Subdomain not found in this domain")

        user = db.query(User).filter_by(id=added_by_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        resource = Resource(
            title=title,
            description=description,
            link=link,
            domain_id=domain_id,
            subdomain_id=subdomain_id,
            added_by_id=added_by_id,
            is_verified=False   # default, can only be updated via moderation
        )
        db.add(resource)
        db.commit()
        db.refresh(resource)

        return {"message": "Resource added successfully", "resource_id": resource.id}

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ✅ Get resources by IDs
@router.post("/by-id")
def get_resources_by_ids(payload: dict, db: Session = Depends(get_db)):
    try:
        domain_id = payload.get("domain_id")
        subdomain_id = payload.get("subdomain_id")

        if not domain_id or not subdomain_id:
            raise HTTPException(status_code=400, detail="Both domain_id and subdomain_id are required")

        resources = db.query(Resource).filter_by(
            domain_id=domain_id, subdomain_id=subdomain_id
        ).all()

        return format_resources(resources)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ✅ Get all resources
@router.get("/all-resources")
def get_all_resources(user_id: int = None, db: Session = Depends(get_db)):
    try:
        resources = db.query(Resource).all()
        return [format_resource(r, db=db, user_id=user_id) for r in resources]
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ✅ Delete resource
@router.delete("/{resource_id}")
def delete_resource(resource_id: int, db: Session = Depends(get_db)):
    try:
        resource = db.query(Resource).filter_by(id=resource_id).first()
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")

        db.delete(resource)
        db.commit()
        return {"message": f"Resource with id {resource_id} deleted successfully"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ✅ Get resource by ID
@router.get("/{resource_id}")
def get_resource_by_id(resource_id: int, db: Session = Depends(get_db)):
    try:
        resource = db.query(Resource).filter_by(id=resource_id).first()
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")

        return format_resource(resource)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ✅ Get resources by user ID
@router.get("/by-user/{user_id}")
def get_resources_by_user(user_id: int, db: Session = Depends(get_db)):
    try:
        # Check if user exists
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        resources = db.query(Resource).filter_by(added_by_id=user_id).all()
        return format_resources(resources)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

from pydantic import BaseModel

class VotePayload(BaseModel):
    user_id: int


# ✅ Upvote

@router.post("/{resource_id}/upvote")
def upvote_resource(resource_id: int, payload: VotePayload, db: Session = Depends(get_db)):
    try:
        resource = db.query(Resource).filter_by(id=resource_id).first()
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")

        existing_vote = db.query(ResourceVote).filter_by(resource_id=resource_id, user_id=payload.user_id).first()

        if existing_vote:
            if existing_vote.vote_type == 1:
                message = "You have already upvoted this resource"
            elif existing_vote.vote_type == -1:
                existing_vote.vote_type = 1
                resource.downvote -= 1
                resource.upvote += 1
                message = "Vote changed to upvote"
        else:
            new_vote = ResourceVote(resource_id=resource_id, user_id=payload.user_id, vote_type=1)
            db.add(new_vote)
            resource.upvote += 1
            message = "Resource upvoted"

        db.commit()
        db.refresh(resource)
        return {"message": message, "upvotes": resource.upvote, "downvotes": resource.downvote}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ✅ Downvote
@router.post("/{resource_id}/downvote")
def downvote_resource(resource_id: int, payload: VotePayload, db: Session = Depends(get_db)):
    try:
        resource = db.query(Resource).filter_by(id=resource_id).first()
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")

        existing_vote = db.query(ResourceVote).filter_by(resource_id=resource_id, user_id=payload.user_id).first()

        if existing_vote:
            if existing_vote.vote_type == -1:
                message = "You have already downvoted this resource"
            elif existing_vote.vote_type == 1:
                existing_vote.vote_type = -1
                resource.upvote -= 1
                resource.downvote += 1
                message = "Vote changed to downvote"
        else:
            new_vote = ResourceVote(resource_id=resource_id, user_id=payload.user_id, vote_type=-1)
            db.add(new_vote)
            resource.downvote += 1
            message = "Resource downvoted"

        db.commit()
        db.refresh(resource)
        return {"message": message, "upvotes": resource.upvote, "downvotes": resource.downvote}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ✅ Update resource (by ID only)
@router.patch("/{resource_id}")
def update_resource(resource_id: int, payload: dict, db: Session = Depends(get_db)):
    try:
        resource = db.query(Resource).filter_by(id=resource_id).first()
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")

        allowed_fields = ["title", "description", "link", "domain_id", "subdomain_id", "is_verified"]
        updated = False
        for field in allowed_fields:
            if field in payload:
                setattr(resource, field, payload[field])
                updated = True

        if not updated:
            return {"message": "No changes applied"}

        db.commit()
        db.refresh(resource)
        return {"message": "Resource updated successfully"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# -----------------------------------------------------------
# 🛠️ Utility for formatting responses consistently
# -----------------------------------------------------------
def format_resource(r: Resource, db: Session = None, user_id: int = None):
    added_by_name = None
    if r.user:
        if r.user.user_details and (r.user.user_details.firstName or r.user.user_details.lastName):
            added_by_name = f"{r.user.user_details.firstName or ''} {r.user.user_details.lastName or ''}".strip()
        else:
            added_by_name = r.user.username

    vote_status = None
    if db and user_id:
        vote = db.query(ResourceVote).filter_by(resource_id=r.id, user_id=user_id).first()
        if vote:
            vote_status = "upvoted" if vote.vote_type == 1 else "downvoted"

    return {
        "id": r.id,
        "title": r.title,
        "description": r.description,
        "link": r.link,
        "upvote": r.upvote,
        "downvote": r.downvote,
        "domain_id": r.domain_id,
        "domain_name": r.domain.name if r.domain else None,
        "subdomain_id": r.subdomain_id,
        "subdomain_name": r.subdomain.name if r.subdomain else None,
        "added_by_id": r.added_by_id,
        "added_by_name": added_by_name,
        "is_verified": r.is_verified,
        "user_vote": vote_status,  # can be 'upvoted', 'downvoted', or None
    }




def format_resources(resources: list[Resource]):
    return [format_resource(r) for r in resources]



# -----------------------------------------------------------
# ➕ Domain Endpoints
# -----------------------------------------------------------
@router.post("/domain")
def create_domain(payload: dict, db: Session = Depends(get_db)):
    try:
        name = payload.get("name")
        if not name:
            raise HTTPException(status_code=400, detail="Domain name is required")

        # Check if exists
        existing = db.query(Domain).filter_by(name=name).first()
        if existing:
            raise HTTPException(status_code=409, detail="Domain already exists")

        domain = Domain(name=name)
        db.add(domain)
        db.commit()
        db.refresh(domain)
        return {"message": "Domain created successfully", "domain_id": domain.id}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/domain/all")
def get_all_domains(db: Session = Depends(get_db)):
    try:
        domains = db.query(Domain).all()
        return [{"id": d.id, "name": d.name} for d in domains]
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# -----------------------------------------------------------
# ➕ Subdomain Endpoints
# -----------------------------------------------------------
@router.post("/subdomain")
def create_subdomain(payload: dict, db: Session = Depends(get_db)):
    try:
        name = payload.get("name")
        domain_id = payload.get("domain_id")

        if not name or not domain_id:
            raise HTTPException(status_code=400, detail="Subdomain name and domain_id are required")

        # Ensure domain exists
        domain = db.query(Domain).filter_by(id=domain_id).first()
        if not domain:
            raise HTTPException(status_code=404, detail="Parent domain not found")

        # Check if exists
        existing = db.query(Subdomain).filter_by(name=name, domain_id=domain_id).first()
        if existing:
            raise HTTPException(status_code=409, detail="Subdomain already exists in this domain")

        subdomain = Subdomain(name=name, domain_id=domain_id)
        db.add(subdomain)
        db.commit()
        db.refresh(subdomain)
        return {"message": "Subdomain created successfully", "subdomain_id": subdomain.id}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/subdomain/all")
def get_all_subdomains(db: Session = Depends(get_db)):
    try:
        subdomains = db.query(Subdomain).all()
        return [
            {"id": s.id, "name": s.name, "domain_id": s.domain_id}
            for s in subdomains
        ]
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/domain/{domain_id}")
def get_domain_by_id(domain_id: int, db: Session = Depends(get_db)):
    try:
        domain = db.query(Domain).filter_by(id=domain_id).first()
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")
        return {"id": domain.id, "name": domain.name}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.patch("/domain/{domain_id}")
def update_domain(domain_id: int, payload: dict, db: Session = Depends(get_db)):
    try:
        domain = db.query(Domain).filter_by(id=domain_id).first()
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")
        name = payload.get("name")
        if name:
            domain.name = name
            db.commit()
            db.refresh(domain)
            return {"message": "Domain updated successfully", "id": domain.id, "name": domain.name}
        return {"message": "No changes applied"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.delete("/domain/{domain_id}")
def delete_domain(domain_id: int, db: Session = Depends(get_db)):
    try:
        domain = db.query(Domain).filter_by(id=domain_id).first()
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")
        db.delete(domain)
        db.commit()
        return {"message": f"Domain with id {domain_id} deleted successfully"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/subdomain/{subdomain_id}")
def get_subdomain_by_id(subdomain_id: int, db: Session = Depends(get_db)):
    try:
        subdomain = db.query(Subdomain).filter_by(id=subdomain_id).first()
        if not subdomain:
            raise HTTPException(status_code=404, detail="Subdomain not found")
        return {"id": subdomain.id, "name": subdomain.name, "domain_id": subdomain.domain_id}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.patch("/subdomain/{subdomain_id}")
def update_subdomain(subdomain_id: int, payload: dict, db: Session = Depends(get_db)):
    try:
        subdomain = db.query(Subdomain).filter_by(id=subdomain_id).first()
        if not subdomain:
            raise HTTPException(status_code=404, detail="Subdomain not found")
        name = payload.get("name")
        if name:
            subdomain.name = name
            db.commit()
            db.refresh(subdomain)
            return {"message": "Subdomain updated successfully", "id": subdomain.id, "name": subdomain.name}
        return {"message": "No changes applied"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete("/subdomain/{subdomain_id}")
def delete_subdomain(subdomain_id: int, db: Session = Depends(get_db)):
    try:
        subdomain = db.query(Subdomain).filter_by(id=subdomain_id).first()
        if not subdomain:
            raise HTTPException(status_code=404, detail="Subdomain not found")
        db.delete(subdomain)
        db.commit()
        return {"message": f"Subdomain with id {subdomain_id} deleted successfully"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/domain/{domain_id}/subdomains")
def get_subdomains_for_domain(domain_id: int, db: Session = Depends(get_db)):
    try:
        subdomains = db.query(Subdomain).filter_by(domain_id=domain_id).all()
        return [
            {"id": s.id, "name": s.name, "domain_id": s.domain_id}
            for s in subdomains
        ]
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
