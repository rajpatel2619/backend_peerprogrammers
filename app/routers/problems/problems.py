from fastapi import APIRouter, Depends, HTTPException, Form, Query
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from ...models.problem_model import (
    CodingProblem, Tag, Company,
    ProblemTag, ProblemCompany, Sheet, SheetProblem, Favorite
)
from ...connection.utility import get_db


router = APIRouter(prefix="/problems", tags=["Problems"])


# ===============================
# TAG CRUD
# ===============================

@router.get("/all/tags")
def get_all_tags(db: Session = Depends(get_db)):
    tags = db.query(Tag).filter(Tag.deleted == False).order_by(Tag.name).all()
    return [
        {"id": t.id, "name": t.name, "created_at": t.created_at, "added_by": t.added_by}
        for t in tags
    ]


@router.post("/create/tag")
def create_tag(tag_name: str, user_id: int, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.name == tag_name).first()

    if tag and not tag.deleted:
        raise HTTPException(400, "Tag already exists")

    if tag and tag.deleted:
        tag.deleted, tag.updated_at, tag.added_by = False, datetime.utcnow(), user_id
    else:
        tag = Tag(name=tag_name, created_at=datetime.utcnow(), added_by=user_id)
        db.add(tag)

    db.commit()
    db.refresh(tag)
    return {"message": "Tag reactivated" if tag.updated_at else "Tag created",
            "tag": {"id": tag.id, "name": tag.name, "added_by": tag.added_by}}


@router.delete("/delete/tag/{tag_id}")
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.id == tag_id, Tag.deleted == False).first()
    if not tag:
        raise HTTPException(404, "Tag not found")

    tag.deleted, tag.updated_at = True, datetime.utcnow()
    db.commit()
    return {"message": f"Tag '{tag.name}' marked as deleted", "tag_id": tag_id}


# ===============================
# COMPANY CRUD
# ===============================
from fastapi import APIRouter, Depends, HTTPException, Form, Query
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload, selectinload
from datetime import datetime
from ...models.problem_model import (
    CodingProblem, Tag, Company,
    ProblemTag, ProblemCompany, Sheet, SheetProblem, Favorite
)
from ...connection.utility import get_db


router = APIRouter(prefix="/problems", tags=["Problems"])


# ===============================
# TAG CRUD
# ===============================

@router.get("/all/tags")
def get_all_tags(db: Session = Depends(get_db)):
    tags = db.query(Tag).filter(Tag.deleted == False).order_by(Tag.name).all()
    return [
        {"id": t.id, "name": t.name, "created_at": t.created_at, "added_by": t.added_by}
        for t in tags
    ]


@router.post("/create/tag")
def create_tag(tag_name: str, user_id: int, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.name == tag_name).first()

    if tag and not tag.deleted:
        raise HTTPException(400, "Tag already exists")

    if tag and tag.deleted:
        tag.deleted, tag.updated_at, tag.added_by = False, datetime.utcnow(), user_id
    else:
        tag = Tag(name=tag_name, created_at=datetime.utcnow(), added_by=user_id)
        db.add(tag)

    db.commit()
    db.refresh(tag)
    return {"message": "Tag reactivated" if tag.updated_at else "Tag created",
            "tag": {"id": tag.id, "name": tag.name, "added_by": tag.added_by}}


@router.delete("/delete/tag/{tag_id}")
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.id == tag_id, Tag.deleted == False).first()
    if not tag:
        raise HTTPException(404, "Tag not found")

    tag.deleted, tag.updated_at = True, datetime.utcnow()
    db.commit()
    return {"message": f"Tag '{tag.name}' marked as deleted", "tag_id": tag_id}


# ===============================
# COMPANY CRUD
# ===============================

@router.post("/create")
def create_company(company_name: str, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.name == company_name).first()

    if company and not company.deleted:
        raise HTTPException(400, "Company already exists")

    if company and company.deleted:
        company.deleted, company.updated_at = False, datetime.utcnow()
    else:
        company = Company(name=company_name, created_at=datetime.utcnow())
        db.add(company)

    db.commit()
    db.refresh(company)
    return {"message": "Company reactivated" if company.updated_at else "Company created",
            "company": {"id": company.id, "name": company.name}}


@router.get("/list")
def list_companies(db: Session = Depends(get_db)):
    companies = db.query(Company).filter(Company.deleted == False).all()
    return {"companies": [{"id": c.id, "name": c.name} for c in companies]}


@router.delete("/{company_id}")
def delete_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id, Company.deleted == False).first()
    if not company:
        raise HTTPException(404, "Company not found")

    company.deleted, company.updated_at = True, datetime.utcnow()
    db.commit()
    return {"message": "Company deleted"}


# ===============================
# PROBLEM CRUD
# ===============================

@router.put("/update_problem/{problem_id}")
def update_problem(
    problem_id: int,
    title: Optional[str] = Form(None),
    link: Optional[str] = Form(None),
    difficulty: Optional[str] = Form(None),
    gitHubLink: Optional[str] = Form(None),
    hindiSolution: Optional[str] = Form(None),
    englishSolution: Optional[str] = Form(None),
    is_premium: Optional[bool] = Form(None),
    tag_ids: Optional[List[int]] = Form(None),
    company_ids: Optional[List[int]] = Form(None),
    sheet_ids: Optional[List[int]] = Form(None),
    db: Session = Depends(get_db)
):
    problem = db.query(CodingProblem).filter(CodingProblem.id == problem_id, CodingProblem.deleted == False).first()
    if not problem:
        raise HTTPException(404, "Problem not found")

    # Update basic fields
    if title:
        # check duplicate title
        existing = db.query(CodingProblem).filter(CodingProblem.title == title, CodingProblem.id != problem_id, CodingProblem.deleted == False).first()
        if existing:
            raise HTTPException(400, "Another problem with this title already exists")
        problem.title = title
    if link:
        problem.link = link
    if difficulty:
        problem.difficulty = difficulty
    if gitHubLink is not None:
        problem.gitHubLink = gitHubLink
    if hindiSolution is not None:
        problem.hindiSolution = hindiSolution
    if englishSolution is not None:
        problem.englishSolution = englishSolution
    if is_premium is not None:
        problem.is_premium = is_premium

    # Update Tags
    if tag_ids is not None:
        # Remove existing associations
        db.query(ProblemTag).filter_by(problem_id=problem_id).delete()
        for tid in tag_ids:
            tag = db.query(Tag).filter_by(id=tid, deleted=False).first()
            if not tag:
                raise HTTPException(404, f"Tag ID not found: {tid}")
            db.add(ProblemTag(problem_id=problem_id, tag_id=tid, created_by=problem.created_by))

    # Update Companies
    if company_ids is not None:
        db.query(ProblemCompany).filter_by(problem_id=problem_id).delete()
        for cid in company_ids:
            company = db.query(Company).filter_by(id=cid, deleted=False).first()
            if not company:
                raise HTTPException(404, f"Company ID not found: {cid}")
            db.add(ProblemCompany(problem_id=problem_id, company_id=cid, created_by=problem.created_by))

    # Update Sheets
    if sheet_ids is not None:
        db.query(SheetProblem).filter_by(problem_id=problem_id).delete()
        for sid in sheet_ids:
            sheet = db.query(Sheet).filter_by(id=sid, deleted=False).first()
            if not sheet:
                raise HTTPException(404, f"Sheet ID not found: {sid}")
            db.add(SheetProblem(problem_id=problem_id, sheet_id=sid, created_by=problem.created_by))

    problem.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(problem)

    return {"message": "Problem updated successfully", "problem_id": problem.id, "sheet":problem}



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
    sheet_ids: Optional[List[int]] = Form(None),
    created_by: int = Form(1),
    db: Session = Depends(get_db)
):
    if db.query(CodingProblem).filter(CodingProblem.title == title, CodingProblem.deleted == False).first():
        raise HTTPException(400, "Problem with this title already exists")

    problem = CodingProblem(
        title=title, link=link, difficulty=difficulty,
        created_at=datetime.utcnow(), created_by=created_by,
        gitHubLink=gitHubLink, hindiSolution=hindiSolution,
        englishSolution=englishSolution, is_premium=is_premium
    )
    db.add(problem)
    db.flush()  # so we get problem.id

    # Attach Tags
    if tag_ids:
        for tid in tag_ids:
            tag = db.query(Tag).filter_by(id=tid, deleted=False).first()
            if not tag:
                raise HTTPException(404, f"Tag ID not found: {tid}")
            db.add(ProblemTag(problem_id=problem.id, tag_id=tid, created_by=created_by))

    # Attach Companies
    if company_ids:
        for cid in company_ids:
            company = db.query(Company).filter_by(id=cid, deleted=False).first()
            if not company:
                raise HTTPException(404, f"Company ID not found: {cid}")
            db.add(ProblemCompany(problem_id=problem.id, company_id=cid, created_by=created_by))

    # Attach Sheets
    if sheet_ids:
        for sid in sheet_ids:
            sheet = db.query(Sheet).filter_by(id=sid, deleted=False).first()
            if not sheet:
                raise HTTPException(404, f"Sheet ID not found: {sid}")
            db.add(SheetProblem(problem_id=problem.id, sheet_id=sid, created_by=created_by))

    db.commit()
    return {"message": "Problem created successfully", "problem_id": problem.id}


@router.get("/all_problem")
def get_all_problems(db: Session = Depends(get_db)):
    problems = db.query(CodingProblem).options(
        selectinload(CodingProblem.tags),
        selectinload(CodingProblem.companies),
        selectinload(CodingProblem.sheets).joinedload(SheetProblem.sheet)
    ).filter(CodingProblem.deleted == False).all()
    return [
        {
            "id": p.id, "title": p.title, "link": p.link, "difficulty": p.difficulty,
            "is_premium": p.is_premium, "created_at": p.created_at, "updated_at": p.updated_at,
            "gitHubLink": p.gitHubLink, "hindiSolution": p.hindiSolution, "englishSolution": p.englishSolution,
            "tags": [t.name for t in p.tags if not t.deleted],
            "companies": [c.name for c in p.companies if not c.deleted],
            "sheets": [
                {"id": sp.sheet.id, "title": sp.sheet.title}
                for sp in p.sheets if not sp.deleted and not sp.sheet.deleted
            ]
        }
        for p in problems
    ]


@router.delete("/deleted_problem/{problem_id}")
def delete_problem(problem_id: int, db: Session = Depends(get_db)):
    problem = db.query(CodingProblem).filter(CodingProblem.id == problem_id, CodingProblem.deleted == False).first()
    if not problem:
        raise HTTPException(404, "Problem not found")
    problem.deleted, problem.updated_at = True, datetime.utcnow()
    db.commit()
    return {"message": "Problem deleted"}


# ===============================
# SHEET CRUD
# ===============================

@router.post("/create_sheet")
def create_sheet(title: str = Form(...), created_by: int = Form(1), db: Session = Depends(get_db)):
    if db.query(Sheet).filter(Sheet.title == title, Sheet.deleted == False).first():
        raise HTTPException(400, "Sheet already exists")
    sheet = Sheet(title=title, created_by=created_by)
    db.add(sheet)
    db.commit()
    db.refresh(sheet)
    return {"message": "Sheet created", "sheet_id": sheet.id, "title": sheet.title}


@router.get("/all_sheets")
def get_all_sheets(db: Session = Depends(get_db)):
    sheets = db.query(Sheet).filter(Sheet.deleted == False).all()
    return [
        {
            "id": s.id, "title": s.title, "created_by": s.created_by, "created_at": s.created_at,
            "problems": [
                {
                    "id": sp.problem.id, "title": sp.problem.title, "link": sp.problem.link,
                    "difficulty": sp.problem.difficulty, "is_premium": sp.problem.is_premium,
                    "created_at": sp.problem.created_at, "updated_at": sp.problem.updated_at,
                    "gitHubLink": sp.problem.gitHubLink, "hindiSolution": sp.problem.hindiSolution,
                    "englishSolution": sp.problem.englishSolution,
                    "tags": [t.name for t in sp.problem.tags if not t.deleted],
                    "companies": [c.name for c in sp.problem.companies if not c.deleted]
                }
                for sp in s.problems if not sp.deleted and not sp.problem.deleted
            ]
        }
        for s in sheets
    ]


@router.get("/sheets/{sheet_id}")
def get_sheet_by_id(sheet_id: int, db: Session = Depends(get_db)):
    sheet = db.query(Sheet).filter(Sheet.id == sheet_id, Sheet.deleted == False).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Sheet not found")
    
    return {
        "id": sheet.id, "title": sheet.title, "created_by": sheet.created_by, "created_at": sheet.created_at,
        "problems": [
            {
                "id": sp.problem.id, "title": sp.problem.title, "link": sp.problem.link,
                "difficulty": sp.problem.difficulty, "is_premium": sp.problem.is_premium,
                "created_at": sp.problem.created_at, "updated_at": sp.problem.updated_at,
                "gitHubLink": sp.problem.gitHubLink, "hindiSolution": sp.problem.hindiSolution,
                "englishSolution": sp.problem.englishSolution,
                "tags": [t.name for t in sp.problem.tags if not t.deleted],
                "companies": [c.name for c in sp.problem.companies if not c.deleted]
            }
            for sp in sheet.problems if not sp.deleted and not sp.problem.deleted
        ]
    }


@router.put("/sheets/{sheet_id}")
def update_sheet(sheet_id: int, title: Optional[str] = Form(None), problem_ids: Optional[List[int]] = Form(None), db: Session = Depends(get_db)):
    sheet = db.query(Sheet).filter(Sheet.id == sheet_id, Sheet.deleted == False).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="Sheet not found")

    if title:
        if db.query(Sheet).filter(Sheet.title == title, Sheet.id != sheet_id, Sheet.deleted == False).first():
            raise HTTPException(status_code=400, detail="A sheet with this title already exists")
        sheet.title = title

    if problem_ids is not None:
        db.query(SheetProblem).filter(SheetProblem.sheet_id == sheet_id).delete()
        for pid in problem_ids:
            problem = db.query(CodingProblem).filter(CodingProblem.id == pid, CodingProblem.deleted == False).first()
            if not problem:
                raise HTTPException(status_code=404, detail=f"Problem with ID {pid} not found or is deleted.")
            db.add(SheetProblem(sheet_id=sheet_id, problem_id=pid, created_by=sheet.created_by))

    db.commit()
    db.refresh(sheet)
    return {"message": "Sheet updated successfully", "sheet_id": sheet.id}


@router.delete("/sheets/{sheet_id}")
def delete_sheet(sheet_id: int, db: Session = Depends(get_db)):
    sheet = db.query(Sheet).filter(Sheet.id == sheet_id, Sheet.deleted == False).first()
    if not sheet:
        raise HTTPException(404, "Sheet not found")
    sheet.deleted = True
    db.commit()
    return {"message": "Sheet deleted"}


# ===============================
# FILTER Problems
# ===============================

@router.get("/filter")
def filter_problems(
    difficulties: Optional[List[str]] = Query(None),
    tag_ids: Optional[List[int]] = Query(None),
    company_ids: Optional[List[int]] = Query(None),
    sheet_ids: Optional[List[int]] = Query(None),
    favorite: bool = Query(False),
    user_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(CodingProblem).options(joinedload(CodingProblem.tags), joinedload(CodingProblem.companies))

    if difficulties:
        query = query.filter(CodingProblem.difficulty.in_(difficulties))
    if tag_ids:
        query = query.join(CodingProblem.tags).filter(Tag.id.in_(tag_ids), Tag.deleted == False)
    if company_ids:
        query = query.join(CodingProblem.companies).filter(Company.id.in_(company_ids))
    if sheet_ids:
        query = query.join(SheetProblem, SheetProblem.problem_id == CodingProblem.id).filter(SheetProblem.sheet_id.in_(sheet_ids))
    if favorite:
        if not user_id:
            raise HTTPException(400, "user_id is required when favorite=true")
        query = query.join(Favorite, Favorite.problem_id == CodingProblem.id).filter(Favorite.user_id == user_id)

    total = query.distinct().count()
    problems = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total, "page": page,
        "results": [
            {
                "id": p.id, "title": p.title, "link": p.link, "difficulty": p.difficulty,
                "created_at": p.created_at, "updated_at": p.updated_at, "created_by": p.created_by,
                "gitHubLink": p.gitHubLink, "hindiSolution": p.hindiSolution, "englishSolution": p.englishSolution,
                "tags": [t.name for t in p.tags if not t.deleted],
                "companies": [c.name for c in p.companies]
            } for p in problems
        ]
    }


@router.get("/filter-options")
def get_filter_options(db: Session = Depends(get_db)):
    companies = [{"id": c.id, "name": c.name} for c in db.query(Company).filter(Company.deleted == False).order_by(Company.name)]
    sheets = [{"id": s.id, "title": s.title} for s in db.query(Sheet).filter(Sheet.deleted == False).order_by(Sheet.title)]
    tags = [{"id": t.id, "name": t.name} for t in db.query(Tag).filter(Tag.deleted == False).order_by(Tag.name)]
    difficulties = [{"id": i+1, "name": d[0]} for i, d in enumerate(db.query(CodingProblem.difficulty).distinct().all()) if d]

    return {"companies": companies, "sheets": sheets, "tags": tags, "difficulties": difficulties}


# ===============================
# FAVORITES
# ===============================

@router.post("/favorite")
def add_favorite(user_id: int = Form(...), problem_id: int = Form(...), db: Session = Depends(get_db)):
    if not db.query(CodingProblem).filter(CodingProblem.id == problem_id).first():
        raise HTTPException(404, "Problem not found")
    if db.query(Favorite).filter_by(user_id=user_id, problem_id=problem_id).first():
        raise HTTPException(400, "Already favorite")

    fav = Favorite(user_id=user_id, problem_id=problem_id, created_at=datetime.utcnow())
    db.add(fav)
    db.commit()
    return {"message": "Added to favorite", "favorite_id": fav.id}


@router.delete("/favorite")
def remove_favorite(user_id: int, problem_id: int, db: Session = Depends(get_db)):
    fav = db.query(Favorite).filter_by(user_id=user_id, problem_id=problem_id).first()
    if not fav:
        raise HTTPException(404, "Favorite record not found")
    db.delete(fav)
    db.commit()
    return {"message": "Removed from favorites"}

@router.post("/create")
def create_company(company_name: str, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.name == company_name).first()

    if company and not company.deleted:
        raise HTTPException(400, "Company already exists")

    if company and company.deleted:
        company.deleted, company.updated_at = False, datetime.utcnow()
    else:
        company = Company(name=company_name, created_at=datetime.utcnow())
        db.add(company)

    db.commit()
    db.refresh(company)
    return {"message": "Company reactivated" if company.updated_at else "Company created",
            "company": {"id": company.id, "name": company.name}}


@router.get("/list")
def list_companies(db: Session = Depends(get_db)):
    companies = db.query(Company).filter(Company.deleted == False).all()
    return {"companies": [{"id": c.id, "name": c.name} for c in companies]}


@router.delete("/{company_id}")
def delete_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id, Company.deleted == False).first()
    if not company:
        raise HTTPException(404, "Company not found")

    company.deleted, company.updated_at = True, datetime.utcnow()
    db.commit()
    return {"message": "Company deleted"}


# ===============================
# PROBLEM CRUD
# ===============================

@router.put("/update_problem/{problem_id}")
def update_problem(
    problem_id: int,
    title: Optional[str] = Form(None),
    link: Optional[str] = Form(None),
    difficulty: Optional[str] = Form(None),
    gitHubLink: Optional[str] = Form(None),
    hindiSolution: Optional[str] = Form(None),
    englishSolution: Optional[str] = Form(None),
    is_premium: Optional[bool] = Form(None),
    tag_ids: Optional[List[int]] = Form(None),
    company_ids: Optional[List[int]] = Form(None),
    sheet_ids: Optional[List[int]] = Form(None),
    db: Session = Depends(get_db)
):
    problem = db.query(CodingProblem).filter(CodingProblem.id == problem_id, CodingProblem.deleted == False).first()
    if not problem:
        raise HTTPException(404, "Problem not found")

    # Update basic fields
    if title:
        # check duplicate title
        existing = db.query(CodingProblem).filter(CodingProblem.title == title, CodingProblem.id != problem_id, CodingProblem.deleted == False).first()
        if existing:
            raise HTTPException(400, "Another problem with this title already exists")
        problem.title = title
    if link:
        problem.link = link
    if difficulty:
        problem.difficulty = difficulty
    if gitHubLink is not None:
        problem.gitHubLink = gitHubLink
    if hindiSolution is not None:
        problem.hindiSolution = hindiSolution
    if englishSolution is not None:
        problem.englishSolution = englishSolution
    if is_premium is not None:
        problem.is_premium = is_premium

    # Update Tags
    if tag_ids is not None:
        # Remove existing associations
        db.query(ProblemTag).filter_by(problem_id=problem_id).delete()
        for tid in tag_ids:
            tag = db.query(Tag).filter_by(id=tid, deleted=False).first()
            if not tag:
                raise HTTPException(404, f"Tag ID not found: {tid}")
            db.add(ProblemTag(problem_id=problem_id, tag_id=tid, created_by=problem.created_by))

    # Update Companies
    if company_ids is not None:
        db.query(ProblemCompany).filter_by(problem_id=problem_id).delete()
        for cid in company_ids:
            company = db.query(Company).filter_by(id=cid, deleted=False).first()
            if not company:
                raise HTTPException(404, f"Company ID not found: {cid}")
            db.add(ProblemCompany(problem_id=problem_id, company_id=cid, created_by=problem.created_by))

    # Update Sheets
    if sheet_ids is not None:
        db.query(SheetProblem).filter_by(problem_id=problem_id).delete()
        for sid in sheet_ids:
            sheet = db.query(Sheet).filter_by(id=sid, deleted=False).first()
            if not sheet:
                raise HTTPException(404, f"Sheet ID not found: {sid}")
            db.add(SheetProblem(problem_id=problem_id, sheet_id=sid, created_by=problem.created_by))

    problem.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(problem)

    return {"message": "Problem updated successfully", "problem_id": problem.id}



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
    sheet_ids: Optional[List[int]] = Form(None),
    created_by: int = Form(1),
    db: Session = Depends(get_db)
):
    if db.query(CodingProblem).filter(CodingProblem.title == title, CodingProblem.deleted == False).first():
        raise HTTPException(400, "Problem with this title already exists")

    problem = CodingProblem(
        title=title, link=link, difficulty=difficulty,
        created_at=datetime.utcnow(), created_by=created_by,
        gitHubLink=gitHubLink, hindiSolution=hindiSolution,
        englishSolution=englishSolution, is_premium=is_premium
    )
    db.add(problem)
    db.flush()  # so we get problem.id

    # Attach Tags
    if tag_ids:
        for tid in tag_ids:
            tag = db.query(Tag).filter_by(id=tid, deleted=False).first()
            if not tag:
                raise HTTPException(404, f"Tag ID not found: {tid}")
            db.add(ProblemTag(problem_id=problem.id, tag_id=tid, created_by=created_by))

    # Attach Companies
    if company_ids:
        for cid in company_ids:
            company = db.query(Company).filter_by(id=cid, deleted=False).first()
            if not company:
                raise HTTPException(404, f"Company ID not found: {cid}")
            db.add(ProblemCompany(problem_id=problem.id, company_id=cid, created_by=created_by))

    # Attach Sheets
    if sheet_ids:
        for sid in sheet_ids:
            sheet = db.query(Sheet).filter_by(id=sid, deleted=False).first()
            if not sheet:
                raise HTTPException(404, f"Sheet ID not found: {sid}")
            db.add(SheetProblem(problem_id=problem.id, sheet_id=sid, created_by=created_by))

    db.commit()
    return {"message": "Problem created successfully", "problem_id": problem.id}


@router.get("/all_problem")
def get_all_problems(db: Session = Depends(get_db)):
    problems = db.query(CodingProblem).filter(CodingProblem.deleted == False).all()
    return [
        {
            "id": p.id, "title": p.title, "link": p.link, "difficulty": p.difficulty,
            "is_premium": p.is_premium, "created_at": p.created_at, "updated_at": p.updated_at,
            "gitHubLink": p.gitHubLink, "hindiSolution": p.hindiSolution, "englishSolution": p.englishSolution,
            "tags": [t.name for t in p.tags if not t.deleted],
            "companies": [c.name for c in p.companies if not c.deleted]
        }
        for p in problems
    ]


@router.delete("/deleted_problem/{problem_id}")
def delete_problem(problem_id: int, db: Session = Depends(get_db)):
    problem = db.query(CodingProblem).filter(CodingProblem.id == problem_id, CodingProblem.deleted == False).first()
    if not problem:
        raise HTTPException(404, "Problem not found")
    problem.deleted, problem.updated_at = True, datetime.utcnow()
    db.commit()
    return {"message": "Problem deleted"}


# ===============================
# SHEET CRUD
# ===============================

@router.post("/create_sheet")
def create_sheet(title: str = Form(...), created_by: int = Form(1), db: Session = Depends(get_db)):
    if db.query(Sheet).filter(Sheet.title == title, Sheet.deleted == False).first():
        raise HTTPException(400, "Sheet already exists")
    sheet = Sheet(title=title, created_by=created_by)
    db.add(sheet)
    db.commit()
    db.refresh(sheet)
    return {"message": "Sheet created", "sheet_id": sheet.id, "title": sheet.title}


@router.get("/all_sheets")
def get_all_sheets(db: Session = Depends(get_db)):
    sheets = db.query(Sheet).filter(Sheet.deleted == False).all()
    return [
        {
            "id": s.id, "title": s.title, "created_by": s.created_by, "created_at": s.created_at,
            "problems": [
                {
                    "id": sp.problem.id, "title": sp.problem.title, "link": sp.problem.link,
                    "difficulty": sp.problem.difficulty, "is_premium": sp.problem.is_premium,
                    "created_at": sp.problem.created_at, "updated_at": sp.problem.updated_at,
                    "gitHubLink": sp.problem.gitHubLink, "hindiSolution": sp.problem.hindiSolution,
                    "englishSolution": sp.problem.englishSolution,
                    "tags": [t.name for t in sp.problem.tags if not t.deleted],
                    "companies": [c.name for c in sp.problem.companies if not c.deleted]
                }
                for sp in s.problems if not sp.deleted and not sp.problem.deleted
            ]
        }
        for s in sheets
    ]


@router.delete("/sheets/{sheet_id}")
def delete_sheet(sheet_id: int, db: Session = Depends(get_db)):
    sheet = db.query(Sheet).filter(Sheet.id == sheet_id, Sheet.deleted == False).first()
    if not sheet:
        raise HTTPException(404, "Sheet not found")
    sheet.deleted = True
    db.commit()
    return {"message": "Sheet deleted"}


# ===============================
# FILTER Problems
# ===============================

@router.get("/filter")
def filter_problems(
    difficulties: Optional[List[str]] = Query(None),
    tag_ids: Optional[List[int]] = Query(None),
    company_ids: Optional[List[int]] = Query(None),
    sheet_ids: Optional[List[int]] = Query(None),
    favorite: bool = Query(False),
    user_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(CodingProblem).options(joinedload(CodingProblem.tags), joinedload(CodingProblem.companies))

    if difficulties:
        query = query.filter(CodingProblem.difficulty.in_(difficulties))
    if tag_ids:
        query = query.join(CodingProblem.tags).filter(Tag.id.in_(tag_ids), Tag.deleted == False)
    if company_ids:
        query = query.join(CodingProblem.companies).filter(Company.id.in_(company_ids))
    if sheet_ids:
        query = query.join(SheetProblem, SheetProblem.problem_id == CodingProblem.id).filter(SheetProblem.sheet_id.in_(sheet_ids))
    if favorite:
        if not user_id:
            raise HTTPException(400, "user_id is required when favorite=true")
        query = query.join(Favorite, Favorite.problem_id == CodingProblem.id).filter(Favorite.user_id == user_id)

    total = query.distinct().count()
    problems = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total, "page": page,
        "results": [
            {
                "id": p.id, "title": p.title, "link": p.link, "difficulty": p.difficulty,
                "created_at": p.created_at, "updated_at": p.updated_at, "created_by": p.created_by,
                "gitHubLink": p.gitHubLink, "hindiSolution": p.hindiSolution, "englishSolution": p.englishSolution,
                "tags": [t.name for t in p.tags if not t.deleted],
                "companies": [c.name for c in p.companies]
            } for p in problems
        ]
    }


@router.get("/filter-options")
def get_filter_options(db: Session = Depends(get_db)):
    companies = [{"id": c.id, "name": c.name} for c in db.query(Company).filter(Company.deleted == False).order_by(Company.name)]
    sheets = [{"id": s.id, "title": s.title} for s in db.query(Sheet).filter(Sheet.deleted == False).order_by(Sheet.title)]
    tags = [{"id": t.id, "name": t.name} for t in db.query(Tag).filter(Tag.deleted == False).order_by(Tag.name)]
    difficulties = [{"id": i+1, "name": d[0]} for i, d in enumerate(db.query(CodingProblem.difficulty).distinct().all()) if d]

    return {"companies": companies, "sheets": sheets, "tags": tags, "difficulties": difficulties}


# ===============================
# FAVORITES
# ===============================

@router.post("/favorite")
def add_favorite(user_id: int = Form(...), problem_id: int = Form(...), db: Session = Depends(get_db)):
    if not db.query(CodingProblem).filter(CodingProblem.id == problem_id).first():
        raise HTTPException(404, "Problem not found")
    if db.query(Favorite).filter_by(user_id=user_id, problem_id=problem_id).first():
        raise HTTPException(400, "Already favorite")

    fav = Favorite(user_id=user_id, problem_id=problem_id, created_at=datetime.utcnow())
    db.add(fav)
    db.commit()
    return {"message": "Added to favorite", "favorite_id": fav.id}


@router.delete("/favorite")
def remove_favorite(user_id: int, problem_id: int, db: Session = Depends(get_db)):
    fav = db.query(Favorite).filter_by(user_id=user_id, problem_id=problem_id).first()
    if not fav:
        raise HTTPException(404, "Favorite record not found")
    db.delete(fav)
    db.commit()
    return {"message": "Removed from favorites"}