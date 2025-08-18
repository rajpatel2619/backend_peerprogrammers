from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from ...connection.utility import get_db
from ...models.resource_model import *

router = APIRouter(prefix="/resources", tags=["Resources"])


# ✅ Create a new resource using IDs
@router.post("/upload-resource")
def create_resource(payload: dict, db: Session = Depends(get_db)):
    try:
        title = payload.get("title")
        description = payload.get("description")
        link = payload.get("link")
        domain_id = payload.get("domain_id")
        subdomain_id = payload.get("subdomain_id")

        if not all([title, link, domain_id, subdomain_id]):
            raise HTTPException(status_code=400, detail="Missing required fields")

        # Validate IDs
        domain = db.query(Domain).filter_by(id=domain_id).first()
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")

        subdomain = db.query(Subdomain).filter_by(id=subdomain_id, domain_id=domain_id).first()
        if not subdomain:
            raise HTTPException(status_code=404, detail="Subdomain not found in this domain")

        resource = Resource(
            title=title,
            description=description,
            link=link,
            domain_id=domain_id,
            subdomain_id=subdomain_id,
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

        resources = db.query(Resource).filter_by(domain_id=domain_id, subdomain_id=subdomain_id).all()

        return [
            {
                "id": r.id,
                "title": r.title,
                "description": r.description,
                "link": r.link,
                "upvote": r.upvote,
                "downvote": r.downvote,
                "domain_id": r.domain_id,
                "subdomain_id": r.subdomain_id
            } for r in resources
        ]

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ✅ Get all resources
@router.get("/all-resources")
def get_all_resources(db: Session = Depends(get_db)):
    try:
        resources = db.query(Resource).all()
        return [
            {
                "id": r.id,
                "title": r.title,
                "description": r.description,
                "link": r.link,
                "upvote": r.upvote,
                "downvote": r.downvote,
                "domain_id": r.domain_id,
                "subdomain_id": r.subdomain_id
            } for r in resources
        ]
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

        return {
            "id": resource.id,
            "title": resource.title,
            "description": resource.description,
            "link": resource.link,
            "upvote": resource.upvote,
            "downvote": resource.downvote,
            "domain_id": resource.domain_id,
            "subdomain_id": resource.subdomain_id
        }

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ✅ Upvote
@router.post("/{resource_id}/upvote")
def upvote_resource(resource_id: int, db: Session = Depends(get_db)):
    try:
        resource = db.query(Resource).filter_by(id=resource_id).first()
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")

        resource.upvote += 1
        db.commit()
        db.refresh(resource)

        return {"message": "Resource upvoted", "upvotes": resource.upvote}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ✅ Downvote
@router.post("/{resource_id}/downvote")
def downvote_resource(resource_id: int, db: Session = Depends(get_db)):
    try:
        resource = db.query(Resource).filter_by(id=resource_id).first()
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")

        resource.downvote += 1
        db.commit()
        db.refresh(resource)

        return {"message": "Resource downvoted", "downvotes": resource.downvote}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ✅ Get all domains
@router.get("/domain/all")
def get_all_domains(db: Session = Depends(get_db)):
    try:
        domains = db.query(Domain).all()
        return [{"id": d.id, "name": d.name} for d in domains]
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ✅ Get all subdomains
@router.get("/subdomain/all")
def get_all_subdomains(db: Session = Depends(get_db)):
    try:
        subdomains = db.query(Subdomain).all()
        return [{"id": s.id, "name": s.name, "domain_id": s.domain_id} for s in subdomains]
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ✅ Update resource (by ID only)
@router.patch("/{resource_id}")
def update_resource(resource_id: int, payload: dict, db: Session = Depends(get_db)):
    try:
        resource = db.query(Resource).filter_by(id=resource_id).first()
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")

        allowed_fields = ["title", "description", "link", "domain_id", "subdomain_id"]
        for field in allowed_fields:
            if field in payload:
                setattr(resource, field, payload[field])

        db.commit()
        db.refresh(resource)
        return {"message": "Resource updated successfully"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ✅ Create domain
@router.post("/domain")
def create_domain(payload: dict, db: Session = Depends(get_db)):
    try:
        name = payload.get("name")
        if not name:
            raise HTTPException(status_code=400, detail="Missing domain name")
        domain = db.query(Domain).filter_by(name=name).first()
        if domain:
            raise HTTPException(status_code=409, detail="Domain already exists")
        domain = Domain(name=name)
        db.add(domain)
        db.commit()
        db.refresh(domain)
        return {"message": "Domain created", "domain_id": domain.id}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ✅ Create subdomain using domain_id
@router.post("/subdomain")
def create_subdomain(payload: dict, db: Session = Depends(get_db)):
    try:
        name = payload.get("name")
        domain_id = payload.get("domain_id")
        if not name or not domain_id:
            raise HTTPException(status_code=400, detail="Missing required fields")
        domain = db.query(Domain).filter_by(id=domain_id).first()
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")
        subdomain = db.query(Subdomain).filter_by(name=name, domain_id=domain.id).first()
        if subdomain:
            raise HTTPException(status_code=409, detail="Subdomain already exists")
        subdomain = Subdomain(name=name, domain_id=domain.id)
        db.add(subdomain)
        db.commit()
        db.refresh(subdomain)
        return {"message": "Subdomain created", "subdomain_id": subdomain.id}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ✅ Get subdomains for a domain by ID
@router.get("/domain/{domain_id}/subdomains")
def get_subdomains_for_domain(domain_id: int, db: Session = Depends(get_db)):
    try:
        domain = db.query(Domain).filter_by(id=domain_id).first()
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")
        subdomains = db.query(Subdomain).filter_by(domain_id=domain.id).all()
        return [{"id": s.id, "name": s.name} for s in subdomains]
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ✅ Update domain by ID (partial)
@router.patch("/domain/{domain_id}")
def update_domain(domain_id: int, payload: dict, db: Session = Depends(get_db)):
    try:
        domain = db.query(Domain).filter_by(id=domain_id).first()
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")

        # Only allow updating name; check for uniqueness
        new_name = payload.get("name")
        if new_name:
            existing = db.query(Domain).filter(Domain.name == new_name, Domain.id != domain_id).first()
            if existing:
                raise HTTPException(status_code=409, detail="Another domain with this name already exists")
            domain.name = new_name

        db.commit()
        db.refresh(domain)
        return {"message": "Domain updated successfully", "domain_id": domain.id, "name": domain.name}

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ✅ Delete domain by ID
@router.delete("/domain/{domain_id}")
def delete_domain(domain_id: int, db: Session = Depends(get_db)):
    try:
        domain = db.query(Domain).filter_by(id=domain_id).first()
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")

        # If you have FK constraints with ON DELETE RESTRICT, block deletion when subdomains/resources exist
        # Option A: Block deletion when children exist
        subdomain_exists = db.query(Subdomain.id).filter_by(domain_id=domain_id).first()
        if subdomain_exists:
            raise HTTPException(status_code=409, detail="Cannot delete domain: subdomains exist under this domain")

        # If Resources reference domain_id directly without cascade, also check:
        resource_exists = db.query(Resource.id).filter_by(domain_id=domain_id).first()
        if resource_exists:
            raise HTTPException(status_code=409, detail="Cannot delete domain: resources exist under this domain")

        db.delete(domain)
        db.commit()
        return {"message": f"Domain {domain_id} deleted successfully"}

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ✅ Update subdomain by ID (partial)
@router.patch("/subdomain/{subdomain_id}")
def update_subdomain(subdomain_id: int, payload: dict, db: Session = Depends(get_db)):
    try:
        subdomain = db.query(Subdomain).filter_by(id=subdomain_id).first()
        if not subdomain:
            raise HTTPException(status_code=404, detail="Subdomain not found")

        updated = False

        # Allow updating name with uniqueness within the same domain
        if "name" in payload and payload["name"]:
            new_name = payload["name"]
            conflict = db.query(Subdomain).filter(
                Subdomain.name == new_name,
                Subdomain.domain_id == subdomain.domain_id,
                Subdomain.id != subdomain_id
            ).first()
            if conflict:
                raise HTTPException(status_code=409, detail="Another subdomain with this name exists in this domain")
            subdomain.name = new_name
            updated = True

        # Optionally allow moving subdomain to a different domain
        if "domain_id" in payload and payload["domain_id"]:
            new_domain_id = payload["domain_id"]
            if new_domain_id != subdomain.domain_id:
                # Validate target domain
                target_domain = db.query(Domain).filter_by(id=new_domain_id).first()
                if not target_domain:
                    raise HTTPException(status_code=404, detail="Target domain not found")

                # Ensure uniqueness in the target domain as well
                conflict = db.query(Subdomain).filter(
                    Subdomain.name == subdomain.name,
                    Subdomain.domain_id == new_domain_id
                ).first()
                if conflict:
                    raise HTTPException(status_code=409, detail="Subdomain with same name exists in target domain")

                # Update related resources’ domain_id if they point via subdomain-domain pair?
                # If Resource has both domain_id and subdomain_id, and they must be consistent,
                # you may enforce consistency in business logic or DB constraints.
                subdomain.domain_id = new_domain_id
                updated = True

        if not updated:
            return {"message": "No changes applied"}

        db.commit()
        db.refresh(subdomain)
        return {
            "message": "Subdomain updated successfully",
            "subdomain_id": subdomain.id,
            "name": subdomain.name,
            "domain_id": subdomain.domain_id
        }

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ✅ Delete subdomain by ID
@router.delete("/subdomain/{subdomain_id}")
def delete_subdomain(subdomain_id: int, db: Session = Depends(get_db)):
    try:
        subdomain = db.query(Subdomain).filter_by(id=subdomain_id).first()
        if not subdomain:
            raise HTTPException(status_code=404, detail="Subdomain not found")

        # Block delete when resources exist under the subdomain (and possibly domain-subdomain pair)
        resource_exists = db.query(Resource.id).filter_by(subdomain_id=subdomain_id).first()
        if resource_exists:
            raise HTTPException(status_code=409, detail="Cannot delete subdomain: resources exist under this subdomain")

        db.delete(subdomain)
        db.commit()
        return {"message": f"Subdomain {subdomain_id} deleted successfully"}

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
