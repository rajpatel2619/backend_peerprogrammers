from fastapi import APIRouter, Depends, HTTPException, Form
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
from ...models.problem_model import (
    CodingProblem, Tag, Company,
    ProblemTag, ProblemCompany, Sheet, SheetProblem, Favorite
)
from ...connection.utility import get_db
from fastapi import Query

router = APIRouter(prefix="/problems", tags=["Problems"])

@router.get("/all/tags")
def get_all_tags(db: Session = Depends(get_db)):
    tags = (
        db.query(Tag)
        .filter(Tag.deleted == False)
        .order_by(Tag.name.asc())
        .all()
    )
    return [
        {
            "id": tag.id,
            "name": tag.name,
            "created_at": tag.created_at,
            "added_by": tag.added_by,
        }
        for tag in tags
    ]

@router.delete("/delete/tag/{tag_id}")
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.id == tag_id, Tag.deleted == False).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    tag.deleted = True
    tag.updated_at = datetime.utcnow()
    db.commit()

    return {"message": f"Tag '{tag.name}' marked as deleted", "tag_id": tag_id}

@router.post("/create/tag")
def create_tag(tag_name: str, db: Session = Depends(get_db)):
    # Check if tag exists (active or deleted)
    existing_tag = db.query(Tag).filter(Tag.name == tag_name).first()

    if existing_tag and not existing_tag.deleted:
        raise HTTPException(status_code=400, detail="Tag already exists")

    if existing_tag and existing_tag.deleted:
        # Reactivate deleted tag
        existing_tag.deleted = False
        existing_tag.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_tag)
        return {"message": "Tag reactivated", "tag": {"id": existing_tag.id, "name": existing_tag.name}}

    # Otherwise create new tag
    new_tag = Tag(name=tag_name, created_at=datetime.utcnow())
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)
    return {"message": "Tag created", "tag": {"id": new_tag.id, "name": new_tag.name}}


# ===============================
# Create Company
# ===============================
@router.post("/create")
def create_company(company_name: str, db: Session = Depends(get_db)):
    existing = db.query(Company).filter(Company.name == company_name).first()

    if existing and not existing.deleted:
        raise HTTPException(status_code=400, detail="Company already exists")

    if existing and existing.deleted:
        existing.deleted = False
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return {"message": "Company reactivated", "company": {"id": existing.id, "name": existing.name}}

    new_company = Company(name=company_name, created_at=datetime.utcnow())
    db.add(new_company)
    db.commit()
    db.refresh(new_company)
    return {"message": "Company created", "company": {"id": new_company.id, "name": new_company.name}}


# ===============================
# List Companies (only active)
# ===============================
@router.get("/list")
def list_companies(db: Session = Depends(get_db)):
    companies = db.query(Company).filter(Company.deleted == False).all()
    return {"companies": [{"id": c.id, "name": c.name} for c in companies]}


# ===============================
# Soft Delete Company
# ===============================
@router.delete("/{company_id}")
def delete_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id, Company.deleted == False).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    company.deleted = True
    company.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Company deleted"}

# =========================================
# Create Problem
# =========================================
@router.post("/create_problem")
def create_problem(
    title: str = Form(...),
    link: str = Form(...),
    difficulty: str = Form(...),
    gitHubLink: Optional[str] = Form(None),
    hindiSolution: Optional[str] = Form(None),
    englishSolution: Optional[str] = Form(None),
    is_premium: bool = Form(False),
    tag_ids: Optional[List[int]] = Form(None),
    company_ids: Optional[List[int]] = Form(None),
    created_by: int = Form(1),
    db: Session = Depends(get_db)
):
    existing = db.query(CodingProblem).filter(CodingProblem.title == title, CodingProblem.deleted == False).first()
    if existing:
        raise HTTPException(status_code=400, detail="Problem with this title already exists")

    new_problem = CodingProblem(
        title=title,
        link=link,
        difficulty=difficulty,
        created_at=datetime.utcnow(),
        created_by=created_by,
        gitHubLink=gitHubLink,
        hindiSolution=hindiSolution,
        englishSolution=englishSolution,
        is_premium=is_premium
    )
    db.add(new_problem)
    db.commit()
    db.refresh(new_problem)

    # Add tags
    if tag_ids:
        for tag_id in tag_ids:
            tag = db.query(Tag).filter(Tag.id == tag_id, Tag.deleted == False).first()
            if not tag:
                raise HTTPException(status_code=404, detail=f"Tag ID {tag_id} not found")
            db.add(ProblemTag(problem_id=new_problem.id, tag_id=tag_id, created_by=created_by))

    # Add companies
    if company_ids:
        for company_id in company_ids:
            comp = db.query(Company).filter(Company.id == company_id, Company.deleted == False).first()
            if not comp:
                raise HTTPException(status_code=404, detail=f"Company ID {company_id} not found")
            db.add(ProblemCompany(problem_id=new_problem.id, company_id=company_id, created_by=created_by))

    db.commit()
    return {"message": "Problem created successfully", "problem_id": new_problem.id}


# =========================================
# Get All Problems (active only)
# =========================================
@router.get("/all_problem")
def get_all_problems(db: Session = Depends(get_db)):
    problems = db.query(CodingProblem).filter(CodingProblem.deleted == False).all()
    return [
        {
            "id": p.id,
            "title": p.title,
            "link": p.link,
            "difficulty": p.difficulty,
            "is_premium": p.is_premium,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
            "gitHubLink": p.gitHubLink,
            "hindiSolution": p.hindiSolution,
            "englishSolution": p.englishSolution,
            "tags": [t.name for t in p.tags if not t.deleted],
            "companies": [c.name for c in p.companies if not c.deleted]
        }
        for p in problems
    ]


# =========================================
# Soft Delete Problem
# =========================================
@router.delete("/deleted_problem/{problem_id}")
def delete_problem(problem_id: int, db: Session = Depends(get_db)):
    problem = db.query(CodingProblem).filter(CodingProblem.id == problem_id, CodingProblem.deleted == False).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    problem.deleted = True
    problem.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Problem deleted"}


# =========================================
# Create Sheet
# =========================================
@router.post("/create_sheet")
def create_sheet(
    title: str = Form(...),
    problem_ids: Optional[List[int]] = Form(None),
    created_by: int = Form(1),
    db: Session = Depends(get_db)
):
    existing = db.query(Sheet).filter(Sheet.title == title, Sheet.deleted == False).first()
    if existing:
        raise HTTPException(status_code=400, detail="Sheet with this title already exists")

    new_sheet = Sheet(title=title, created_by=created_by)
    db.add(new_sheet)
    db.commit()
    db.refresh(new_sheet)

    if problem_ids:
        for pid in problem_ids:
            problem = db.query(CodingProblem).filter(CodingProblem.id == pid, CodingProblem.deleted == False).first()
            if not problem:
                raise HTTPException(status_code=404, detail=f"Problem ID {pid} not found")
            db.add(SheetProblem(sheet_id=new_sheet.id, problem_id=pid, created_by=created_by))

    db.commit()
    return {
        "message": "Sheet created successfully",
        "sheet_id": new_sheet.id,
        "title": new_sheet.title,
        "problems_added": problem_ids or []
    }


# =========================================
# Get All Sheets (active only)
# =========================================
@router.get("/all_sheets")
def get_all_sheets(db: Session = Depends(get_db)):
    sheets = db.query(Sheet).filter(Sheet.deleted == False).all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "created_by": s.created_by,
            "created_at": s.created_at,
            "problems": [
                {
                    "id": sp.problem.id,
                    "title": sp.problem.title,
                    "link": sp.problem.link,
                    "difficulty": sp.problem.difficulty,
                    "is_premium": sp.problem.is_premium,
                    "created_at": sp.problem.created_at,
                    "updated_at": sp.problem.updated_at,
                    "gitHubLink": sp.problem.gitHubLink,
                    "hindiSolution": sp.problem.hindiSolution,
                    "englishSolution": sp.problem.englishSolution,
                    "tags": [t.name for t in sp.problem.tags if not t.deleted],
                    "companies": [c.name for c in sp.problem.companies if not c.deleted]
                }
                for sp in s.problems if not sp.deleted and not sp.problem.deleted
            ]
        }
        for s in sheets
    ]


# =========================================
# Soft Delete Sheet
# =========================================
@router.delete("/sheets/{sheet_id}")
def delete_sheet(sheet_id: int, db: Session = Depends(get_db)):
    sheet = db.query(Sheet).filter(Sheet.id == sheet_id, Sheet.deleted == False).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Sheet not found")

    sheet.deleted = True
    db.commit()
    return {"message": "Sheet deleted"}


from fastapi import Query, Form, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from datetime import datetime

# =========================================
# Filter Problems
# =========================================
@router.get("/filter")
def filter_problems(
    difficulties: Optional[List[str]] = Query(None, description="List of difficulty levels"),
    tag_ids: Optional[List[int]] = Query(None, description="List of Tag IDs"),
    company_ids: Optional[List[int]] = Query(None, description="List of Company IDs"),
    sheet_ids: Optional[List[int]] = Query(None, description="List of Sheet IDs"),
    favorite: Optional[bool] = Query(False, description="If true, fetch only user's favorite problems"),
    user_id: Optional[int] = Query(None, description="User ID (required if favorite=true)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(CodingProblem).options(
        joinedload(CodingProblem.tags),
        joinedload(CodingProblem.companies),
    )

    # Filter by difficulty
    if difficulties:
        query = query.filter(CodingProblem.difficulty.in_(difficulties))

    # Filter by tags (ignore deleted tags)
    if tag_ids:
        query = (
            query.join(CodingProblem.tags)
                 .filter(Tag.id.in_(tag_ids), Tag.deleted == False)
        )

    # Filter by companies
    if company_ids:
        query = query.join(CodingProblem.companies).filter(Company.id.in_(company_ids))

    # Filter by sheets
    if sheet_ids:
        query = (
            query.join(SheetProblem, SheetProblem.problem_id == CodingProblem.id)
                 .filter(SheetProblem.sheet_id.in_(sheet_ids))
        )

    # Filter by favorites
    if favorite:
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required when favorite=true")
        query = (
            query.join(Favorite, Favorite.problem_id == CodingProblem.id)
                 .filter(Favorite.user_id == user_id)
        )

    query = query.distinct()

    total = query.count()
    problems = query.offset((page - 1) * page_size).limit(page_size).all()

    results = []
    for p in problems:
        results.append({
            "id": p.id,
            "title": p.title,
            "link": p.link,
            "difficulty": p.difficulty,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
            "created_by": p.created_by,
            "gitHubLink": p.gitHubLink,
            "hindiSolution": p.hindiSolution,
            "englishSolution": p.englishSolution,
            "tags": [t.name for t in p.tags if not t.deleted],   # only active tags
            "companies": [c.name for c in p.companies]
        })

    return {"total": total, "page": page, "results": results}


# =========================================
# Filter Options
# =========================================
@router.get("/filter-options")
def get_filter_options(db: Session = Depends(get_db)):
    """
    Returns all IDs and names for companies, sheets, tags, and available difficulties.
    Useful for building filters in the frontend.
    """

    # Companies
    companies = db.query(Company).order_by(Company.name.asc()).all()
    companies_data = [{"id": c.id, "name": c.name} for c in companies if not getattr(c, "deleted", False)]

    # Sheets
    sheets = db.query(Sheet).order_by(Sheet.title.asc()).all()
    sheets_data = [{"id": s.id, "title": s.title} for s in sheets if not getattr(s, "deleted", False)]

    # Tags (ignore deleted ones)
    tags = db.query(Tag).filter(Tag.deleted == False).order_by(Tag.name.asc()).all()
    tags_data = [{"id": t.id, "name": t.name} for t in tags]

    # Difficulties (get unique values from problems table)
    difficulties = db.query(CodingProblem.difficulty).distinct().all()
    difficulties_list = sorted({d[0] for d in difficulties if d[0]})

    difficulties_data = [{"id": idx + 1, "name": diff} for idx, diff in enumerate(difficulties_list)]

    return {
        "companies": companies_data,
        "sheets": sheets_data,
        "tags": tags_data,
        "difficulties": difficulties_data
    }


# =========================================
# Add Favorite
# =========================================
@router.post("/favorite")
def add_favorite(
    user_id: int = Form(...),
    problem_id: int = Form(...),
    db: Session = Depends(get_db)
):
    problem = db.query(CodingProblem).filter(CodingProblem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    existing_fav = db.query(Favorite).filter_by(user_id=user_id, problem_id=problem_id).first()
    if existing_fav:
        raise HTTPException(status_code=400, detail="Problem is already marked as favorite")

    fav = Favorite(user_id=user_id, problem_id=problem_id, created_at=datetime.utcnow())
    db.add(fav)
    db.commit()
    db.refresh(fav)

    return {
        "message": "Problem marked as favorite successfully",
        "favorite_id": fav.id,
        "user_id": user_id,
        "problem_id": problem_id
    }


# =========================================
# Remove Favorite
# =========================================
@router.delete("/favorite")
def remove_favorite(
    user_id: int,
    problem_id: int,
    db: Session = Depends(get_db)
):
    fav = db.query(Favorite).filter_by(user_id=user_id, problem_id=problem_id).first()
    if not fav:
        raise HTTPException(status_code=404, detail="Favorite record not found")

    db.delete(fav)
    db.commit()

    return {
        "message": "Problem removed from favorites successfully",
        "user_id": user_id,
        "problem_id": problem_id
    }