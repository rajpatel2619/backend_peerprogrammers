from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...connection.utility import get_db
from ...models.resource_model import *
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter()


@router.post("/upload-resource")
def create_resource(payload: dict, db: Session = Depends(get_db)):
    try:

        title = payload.get("title")
        description = payload.get("description")
        link = payload.get("link")
        domain_name = payload.get("domain_name")
        subdomain_name = payload.get("subdomain_name")

        if not all([title, link, domain_name, subdomain_name]):
            raise HTTPException(status_code=400, detail="Missing required fields")

        domain = db.query(Domain).filter_by(name=domain_name).first()
        if not domain:
            domain = Domain(name=domain_name)
            db.add(domain)
            db.commit()
            db.refresh(domain)

        subdomain = db.query(Subdomain).filter_by(
            name=subdomain_name, domain_id=domain.id
        ).first()
        if not subdomain:
            subdomain = Subdomain(name=subdomain_name, domain_id=domain.id)
            db.add(subdomain)
            db.commit()
            db.refresh(subdomain)

        resource = Resource(
            title=title,
            description=description,
            link=link,
            domain_id=domain.id,
            subdomain_id=subdomain.id,
        )
        db.add(resource)
        db.commit()
        db.refresh(resource)

        return {
            "message": "Resource added successfully",
            "resource_id": resource.id
        }

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/get-resources")
def filter_resources(payload: dict, db: Session = Depends(get_db)):
    try:
        domain_name = payload.get("domain_name")
        subdomain_name = payload.get("subdomain_name")

        if not domain_name or not subdomain_name:
            raise HTTPException(status_code=400, detail="Both domain_name and subdomain_name are required")

        domain = db.query(Domain).filter_by(name=domain_name).first()
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")

        subdomain = db.query(Subdomain).filter_by(
            name=subdomain_name, domain_id=domain.id
        ).first()
        if not subdomain:
            raise HTTPException(status_code=404, detail="Subdomain not found")

        resources = db.query(Resource).filter_by(
            domain_id=domain.id, subdomain_id=subdomain.id
        ).all()

        return [
            {
                "id": r.id,
                "title": r.title,
                "description": r.description,
                "link": r.link,
                "upvote": r.upvote,
                "downvote": r.downvote
            } for r in resources
        ]

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


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
                "domain_name": r.domain.name if r.domain else None,
                "subdomain_name": r.subdomain.name if r.subdomain else None
            } for r in resources
        ]
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete("/resources/{resource_id}")
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

@router.get("/resources/{resource_id}")
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
            "domain_name": resource.domain.name if resource.domain else None,
            "subdomain_name": resource.subdomain.name if resource.subdomain else None
        }

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/resources/{resource_id}/upvote")
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


@router.post("/resources/{resource_id}/downvote")
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


@router.get("/resources/domain/all")
def get_all_domains(db: Session = Depends(get_db)):
    try:
        domains = db.query(Domain).all()
        return [d.name for d in domains]
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/resources/subdomain/all")
def get_all_subdomains(db: Session = Depends(get_db)):
    try:
        subdomains = db.query(Subdomain).all()
        return [s.name for s in subdomains]
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
