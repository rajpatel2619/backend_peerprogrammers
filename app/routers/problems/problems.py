from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ...models.problem_model import (
    CodingProblem, Tag, Company,
    ProblemTag, ProblemCompany, Sheet,
    SheetProblem, Favorite
)
from ...connection.utility import get_db

router = APIRouter(prefix="/problems", tags=["Problems"])

@router.get("/")
def list_problems(db: Session = Depends(get_db)):
    problems = db.query(CodingProblem).all()
    return problems

@router.get("/{problem_id}")
def get_problem(problem_id: int, db: Session = Depends(get_db)):
    problem = db.query(CodingProblem).filter(CodingProblem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem

@router.put("/{problem_id}")
def update_problem(problem_id: int, payload: dict, db: Session = Depends(get_db)):
    problem = db.query(CodingProblem).filter(CodingProblem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    for key, value in payload.items():
        if hasattr(problem, key) and value is not None:
            setattr(problem, key, value)

    db.commit()
    db.refresh(problem)
    return {"message": "Problem updated successfully", "problem": problem}

@router.delete("/{problem_id}")
def delete_problem(problem_id: int, db: Session = Depends(get_db)):
    problem = db.query(CodingProblem).filter(CodingProblem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    db.delete(problem)
    db.commit()
    return {"message": "Problem deleted successfully"}

# ===========================
# Tags
# ===========================
@router.get("/tags/all")
def list_tags(db: Session = Depends(get_db)):
    return db.query(Tag).all()

@router.get("/tags/{tag_id}")
def get_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag

@router.put("/tags/{tag_id}")
def update_tag(tag_id: int, payload: dict, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    name = payload.get("name")
    if name:
        tag.name = name
    db.commit()
    db.refresh(tag)
    return {"message": "Tag updated successfully", "tag": tag}

@router.delete("/tags/{tag_id}")
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    db.delete(tag)
    db.commit()
    return {"message": "Tag deleted successfully"}

# ===========================
# Companies
# ===========================
@router.post("/add_company")
def create_company(payload: dict, db: Session = Depends(get_db)):
    name = payload.get("name")
    created_by = payload.get("createdBy")
    if not name:
        raise HTTPException(status_code=400, detail="Company name is required")
    if not created_by:
        raise HTTPException(status_code=400, detail="createdBy (user ID) is required")

    existing = db.query(Company).filter(Company.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Company already exists")

    company = Company(name=name, added_by=created_by, created_at=datetime.utcnow())
    db.add(company)
    db.commit()
    db.refresh(company)
    return {"message": "Company created successfully", "company": company}

@router.get("/companies/all")
def list_companies(db: Session = Depends(get_db)):
    return db.query(Company).all()

@router.put("/companies/{company_id}")
def update_company(company_id: int, payload: dict, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    name = payload.get("name")
    if name:
        company.name = name
    db.commit()
    db.refresh(company)
    return {"message": "Company updated successfully", "company": company}

@router.delete("/companies/{company_id}")
def delete_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(company)
    db.commit()
    return {"message": "Company deleted successfully"}

# ===========================
# Sheets
# ===========================
@router.post("/add_sheet")
def create_sheet(payload: dict, db: Session = Depends(get_db)):
    title = payload.get("title")
    created_by = payload.get("createdBy")
    if not title or not created_by:
        raise HTTPException(status_code=400, detail="title and createdBy are required")
    sheet = Sheet(
        title=title,
        created_by=created_by
    )
    db.add(sheet)
    db.commit()
    db.refresh(sheet)
    return {"message": "Sheet created successfully", "sheet": sheet}

@router.post("/sheet/{sheet_id}/add_problem")
def add_problem_to_sheet(sheet_id: int, payload: dict, db: Session = Depends(get_db)):
    problem_id = payload.get("problem_id")
    created_by = payload.get("createdBy")
    if not problem_id or not created_by:
        raise HTTPException(status_code=400, detail="problem_id and createdBy are required")
    if not db.query(Sheet).filter(Sheet.id == sheet_id).first():
        raise HTTPException(status_code=404, detail="Sheet not found")
    if not db.query(CodingProblem).filter(CodingProblem.id == problem_id).first():
        raise HTTPException(status_code=404, detail="Problem not found")
    mapping = SheetProblem(sheet_id=sheet_id, problem_id=problem_id, created_by=created_by)
    db.add(mapping)
    db.commit()
    return {"message": "Problem added to sheet successfully"}

@router.get("/sheets/all")
def list_sheets(db: Session = Depends(get_db)):
    return db.query(Sheet).all()

# ===========================
# Favorites
# ===========================
@router.post("/favorite/add")
def add_favorite(payload: dict, db: Session = Depends(get_db)):
    user_id = payload.get("user_id")
    problem_id = payload.get("problem_id")
    if not user_id or not problem_id:
        raise HTTPException(status_code=400, detail="user_id and problem_id are required")
    favorite = Favorite(user_id=user_id, problem_id=problem_id)
    db.add(favorite)
    db.commit()
    return {"message": "Favorite added successfully"}

@router.delete("/favorite/remove")
def remove_favorite(payload: dict, db: Session = Depends(get_db)):
    user_id = payload.get("user_id")
    problem_id = payload.get("problem_id")
    fav = db.query(Favorite).filter(Favorite.user_id == user_id, Favorite.problem_id == problem_id).first()
    if not fav:
        raise HTTPException(status_code=404, detail="Favorite not found")
    db.delete(fav)
    db.commit()
    return {"message": "Favorite removed successfully"}

@router.get("/favorite/user/{user_id}")
def list_favorites_for_user(user_id: int, db: Session = Depends(get_db)):
    return db.query(Favorite).filter(Favorite.user_id == user_id).all()

@router.post("/add_tag")
def create_tag(payload: dict, db: Session = Depends(get_db)):
    name = payload.get("name")
    created_by = payload.get("createdBy")
    if not name:
        raise HTTPException(status_code=400, detail="Tag name is required")
    if not created_by:
        raise HTTPException(status_code=400, detail="createdBy (user ID) is required")

    existing = db.query(Tag).filter(Tag.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tag already exists")

    tag = Tag(name=name, added_by=created_by, created_at=datetime.utcnow())
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return {"message": "Tag created successfully", "tag": tag}

@router.post("/add_problem")
def create_problem(payload: dict, db: Session = Depends(get_db)):
    title = payload.get("title")
    link = payload.get("link")  # <-- required!
    difficulty = payload.get("difficulty")
    created_by = payload.get("createdBy")
    tags = payload.get("tags", [])
    companies = payload.get("companies", [])

    if not title or not created_by or not link or not difficulty:
        raise HTTPException(status_code=400, detail="title, link, difficulty, and createdBy are required")

    problem = CodingProblem(
        title=title,
        link=link,   # <-- required!
        difficulty=difficulty,
        created_by=created_by
    )
    db.add(problem)
    db.commit()
    db.refresh(problem)

    # Add tags
    for tag_id in tags:
        if db.query(Tag).filter(Tag.id == tag_id).first():
            db.add(ProblemTag(problem_id=problem.id, tag_id=tag_id))

    # Add companies
    for company_id in companies:
        if db.query(Company).filter(Company.id == company_id).first():
            db.add(ProblemCompany(problem_id=problem.id, company_id=company_id))

    db.commit()
    return {"message": "Problem created successfully", "problem": problem}
