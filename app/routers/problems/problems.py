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


# =========================================
# Create Tag
# =========================================
# Route: Create a new tag in the database
# Method: POST
# Input: Tag name
# Output: Confirmation message with tag details
@router.post("/create/tag")
def create_tag(
    name: str,
    db: Session = Depends(get_db),
    current_user_id: int = 2  # Replace with auth later
):
    existing = db.query(Tag).filter(Tag.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tag already exists")

    tag = Tag(
        name=name,
        added_by=current_user_id,
        created_at=datetime.utcnow()
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return {"message": "Tag created", "tag": {"id": tag.id, "name": tag.name}}


# =========================================
# Create Company
# =========================================
# Route: Create a new company in the database
# Method: POST
# Input: Company name
# Output: Confirmation message with company details
@router.post("/create/company")
def create_company(
    name: str,
    db: Session = Depends(get_db),
    current_user_id: int = 2  # Replace with auth later
):
    existing = db.query(Company).filter(Company.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Company already exists")

    company = Company(
        name=name,
        added_by=current_user_id,
        created_at=datetime.utcnow()
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return {"message": "Company created", "company": {"id": company.id, "name": company.name}}


# =========================================
# Get All Tags
# =========================================
# Route: Fetch all tags from the database
# Method: GET
# Output: List of tags with their details
@router.get("/all/tags")
def get_all_tags(db: Session = Depends(get_db)):
    tags = db.query(Tag).order_by(Tag.name.asc()).all()
    return [
        {"id": tag.id, "name": tag.name, "created_at": tag.created_at, "added_by": tag.added_by}
        for tag in tags
    ]


# =========================================
# Get All Companies
# =========================================
# Route: Fetch all companies from the database
# Method: GET
# Output: List of companies with their details
@router.get("/all/companies")
def get_all_companies(db: Session = Depends(get_db)):
    companies = db.query(Company).order_by(Company.name.asc()).all()
    return [
        {"id": comp.id, "name": comp.name, "created_at": comp.created_at, "added_by": comp.added_by}
        for comp in companies
    ]


# =========================================
# Create Problem
# =========================================
# Route: Create a new coding problem with optional tags and companies
# Method: POST
# Input: Problem details (title, link, difficulty, solutions, tags, companies)
# Output: Confirmation message with problem ID
@router.post("/create/problem")
def create_problem(
    title: str = Form(...),
    link: str = Form(...),
    difficulty: str = Form(...),
    gitHubLink: Optional[str] = Form(None),
    hindiSolution: Optional[str] = Form(None),
    englishSolution: Optional[str] = Form(None),
    tag_ids: Optional[List[int]] = Form(None),
    company_ids: Optional[List[int]] = Form(None),
    created_by: int = Form(1),
    db: Session = Depends(get_db)
):
    # Check for duplicate problem title
    if db.query(CodingProblem).filter(CodingProblem.title == title).first():
        raise HTTPException(status_code=400, detail="Problem with this title already exists")

    # Create problem entry
    new_problem = CodingProblem(
        title=title,
        link=link,
        difficulty=difficulty,
        created_at=datetime.utcnow(),
        created_by=created_by,
        gitHubLink=gitHubLink,
        hindiSolution=hindiSolution,
        englishSolution=englishSolution
    )
    db.add(new_problem)
    db.commit()
    db.refresh(new_problem)

    # Add tags
    if tag_ids:
        for tag_id in tag_ids:
            tag = db.query(Tag).filter(Tag.id == tag_id).first()
            if not tag:
                raise HTTPException(status_code=404, detail=f"Tag ID {tag_id} not found")
            db.add(ProblemTag(problem_id=new_problem.id, tag_id=tag_id, created_by=created_by))

    # Add companies
    if company_ids:
        for company_id in company_ids:
            comp = db.query(Company).filter(Company.id == company_id).first()
            if not comp:
                raise HTTPException(status_code=404, detail=f"Company ID {company_id} not found")
            db.add(ProblemCompany(problem_id=new_problem.id, company_id=company_id, created_by=created_by))

    db.commit()

    return {
        "message": "Problem created successfully",
        "problem_id": new_problem.id
    }


# =========================================
# Get All Problems
# =========================================
# Route: Retrieve all coding problems with tags and company names
# Method: GET
# Output: List of problems with their details, tags, and companies
@router.get("/all")
def get_all_problems(db: Session = Depends(get_db)):
    problems = db.query(CodingProblem).all()
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
            "tags": [t.name for t in p.tags],
            "companies": [c.name for c in p.companies]
        })
    return results


# =========================================
# Create Sheet
# =========================================
# Route: Create a new problem sheet with optional list of problem IDs
# Method: POST
# Input: Sheet title and optional list of problems to link
# Output: Confirmation message with sheet details and linked problems
@router.post("/create/sheet")
def create_sheet(
    title: str = Form(...),
    problem_ids: Optional[List[int]] = Form(None),  # optional list of problems to link
    created_by: int = Form(1),
    db: Session = Depends(get_db)
):
    # Check for duplicate sheet title
    existing_sheet = db.query(Sheet).filter(Sheet.title == title).first()
    if existing_sheet:
        raise HTTPException(status_code=400, detail="Sheet with this title already exists")

    # Create sheet entry
    new_sheet = Sheet(
        title=title,
        created_by=created_by
    )
    db.add(new_sheet)
    db.commit()
    db.refresh(new_sheet)

    # Add problems to sheet if provided
    if problem_ids:
        for pid in problem_ids:
            problem_exists = db.query(CodingProblem).filter(CodingProblem.id == pid).first()
            if not problem_exists:
                raise HTTPException(status_code=404, detail=f"Problem ID {pid} not found")
            db.add(SheetProblem(sheet_id=new_sheet.id, problem_id=pid, created_by=created_by))
        db.commit()

    return {
        "message": "Sheet created successfully",
        "sheet_id": new_sheet.id,
        "title": new_sheet.title,
        "problems_added": problem_ids if problem_ids else []
    }


# =========================================
# Get All Sheets
# =========================================
# Route: Retrieve all sheets with their problems, tags, and companies
# Method: GET
# Output: List of sheets with problem details included
@router.get("/all/sheets")
def get_all_sheets(db: Session = Depends(get_db)):
    sheets = db.query(Sheet).all()
    results = []
    for sheet in sheets:
        results.append({
            "id": sheet.id,
            "title": sheet.title,
            "created_by": sheet.created_by,
            "created_at": sheet.created_at,
            "problems": [
                {
                    "id": sp.problem.id,
                    "title": sp.problem.title,
                    "link": sp.problem.link,
                    "difficulty": sp.problem.difficulty,
                    "created_at": sp.problem.created_at,
                    "updated_at": sp.problem.updated_at,
                    "created_by": sp.problem.created_by,
                    "gitHubLink": sp.problem.gitHubLink,
                    "hindiSolution": sp.problem.hindiSolution,
                    "englishSolution": sp.problem.englishSolution,
                    "tags": [t.name for t in sp.problem.tags],
                    "companies": [c.name for c in sp.problem.companies]
                }
                for sp in sheet.problems
            ]
        })
    return results


@router.get("/filter")
def filter_problems(
    difficulties: Optional[List[str]] = Query(None, description="List of difficulty levels"),
    tag_ids: Optional[List[int]] = Query(None, description="List of Tag IDs"),
    company_ids: Optional[List[int]] = Query(None, description="List of Company IDs"),
    sheet_ids: Optional[List[int]] = Query(None, description="List of Sheet IDs"),
    favorite: Optional[bool] = Query(False, description="If true, fetch only user's favorite problems"),
    user_id: Optional[int] = Query(None, description="User ID (required if favorite=true)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Filter problems by difficulties, tags, companies, sheets,
    and optionally only return user's favorite problems, with pagination.
    """
    query = db.query(CodingProblem)

    # Filter by difficulty
    if difficulties:
        query = query.filter(CodingProblem.difficulty.in_(difficulties))

    # Filter by tags
    if tag_ids:
        query = query.join(CodingProblem.tags).filter(Tag.id.in_(tag_ids))

    # Filter by companies
    if company_ids:
        query = query.join(CodingProblem.companies).filter(Company.id.in_(company_ids))

    # Filter by sheets
    if sheet_ids:
        query = query.join(SheetProblem, SheetProblem.problem_id == CodingProblem.id)\
                     .filter(SheetProblem.sheet_id.in_(sheet_ids))

    # Filter by favorites
    if favorite:
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required when favorite=true")
        query = query.join(Favorite, Favorite.problem_id == CodingProblem.id)\
                     .filter(Favorite.user_id == user_id)

    # Remove duplicates
    query = query.distinct()

    # Pagination
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
            "tags": [t.name for t in p.tags],
            "companies": [c.name for c in p.companies]
        })

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": results
    }




@router.get("/filter-options")
def get_filter_options(db: Session = Depends(get_db)):
    """
    Returns all IDs and names for companies, sheets, tags, and available difficulties.
    Useful for building filters in the frontend.
    """

    # Companies
    companies = db.query(Company).order_by(Company.name.asc()).all()
    companies_data = [{"id": c.id, "name": c.name} for c in companies]

    # Sheets
    sheets = db.query(Sheet).order_by(Sheet.title.asc()).all()
    sheets_data = [{"id": s.id, "title": s.title} for s in sheets]

    # Tags
    tags = db.query(Tag).order_by(Tag.name.asc()).all()
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



@router.post("/favorite")
def add_favorite(
    user_id: int = Form(...),
    problem_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    Marks a coding problem as a favorite for a given user.
    """

    # Check if problem exists
    problem = db.query(CodingProblem).filter(CodingProblem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    # Check if already marked favorite
    existing_fav = db.query(Favorite).filter_by(user_id=user_id, problem_id=problem_id).first()
    if existing_fav:
        raise HTTPException(status_code=400, detail="Problem is already marked as favorite")

    # Add new favorite
    fav = Favorite(
        user_id=user_id,
        problem_id=problem_id,
        created_at=datetime.utcnow()
    )
    db.add(fav)
    db.commit()
    db.refresh(fav)

    return {
        "message": "Problem marked as favorite successfully",
        "favorite_id": fav.id,
        "user_id": user_id,
        "problem_id": problem_id
    }


@router.delete("/favorite")
def remove_favorite(
    user_id: int,
    problem_id: int,
    db: Session = Depends(get_db)
):
    """
    Removes a coding problem from a user's favorites.
    """

    # Check if favorite exists
    fav = db.query(Favorite).filter_by(user_id=user_id, problem_id=problem_id).first()
    if not fav:
        raise HTTPException(status_code=404, detail="Favorite record not found")

    # Delete favorite record
    db.delete(fav)
    db.commit()

    return {
        "message": "Problem removed from favorites successfully",
        "user_id": user_id,
        "problem_id": problem_id
    }
