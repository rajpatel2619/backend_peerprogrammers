from fastapi import APIRouter, Depends, HTTPException, Query, Form, status
from sqlalchemy.orm import Session
from sqlalchemy import func, asc, desc
from typing import Optional, List
from datetime import datetime


from ...models.codeforces_ladder_model import *
from ...models.user_model import User
from ...connection.utility import get_db

router = APIRouter(prefix="/cp51", tags=["CP51"])

# Helpers
def parse_int(value: Optional[str]) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid integer: {value}")

def apply_filters(query,
                  title: Optional[str],
                  difficulty: Optional[str],
                  min_rating: Optional[int],
                  max_rating: Optional[int],
                  is_premium: Optional[bool],
                  created_by: Optional[int]):
    if title:
        query = query.filter(CP51Problem.title.ilike(f"%{title}%"))
    if difficulty:
        query = query.filter(func.lower(CP51Problem.difficulty) == difficulty.lower())
    if min_rating is not None:
        query = query.filter(CP51Problem.rating >= min_rating)
    if max_rating is not None:
        query = query.filter(CP51Problem.rating <= max_rating)
    if is_premium is not None:
        query = query.filter(CP51Problem.is_premium == is_premium)
    if created_by is not None:
        query = query.filter(CP51Problem.created_by == created_by)
    return query

ALLOWED_SORT_FIELDS = {
    "id": CP51Problem.id,
    "title": CP51Problem.title,
    "difficulty": CP51Problem.difficulty,
    "rating": CP51Problem.rating,
    "created_at": CP51Problem.created_at,
}

def apply_sort(query, sort_by: str, sort_order: str):
    col = ALLOWED_SORT_FIELDS.get(sort_by, CP51Problem.created_at)
    return query.order_by(asc(col) if sort_order.lower() == "asc" else desc(col))

# CREATE (POST form)
@router.post("/problems", status_code=status.HTTP_201_CREATED)
def create_problem(
    title: str = Form(..., max_length=255),
    problem_link: str = Form(..., max_length=500),
    difficulty: Optional[str] = Form(None, max_length=50),
    rating: Optional[str] = Form(None),  # will parse to int
    description: Optional[str] = Form(None),
    github_solution_link: Optional[str] = Form(None, max_length=500),
    hindi_solution_link: Optional[str] = Form(None, max_length=500),
    english_solution_link: Optional[str] = Form(None, max_length=500),
    created_by: Optional[str] = Form(None),  # if you pass it from client
    is_premium: Optional[bool] = Form(False),
    db: Session = Depends(get_db),
):
    item = CP51Problem(
        title=title.strip(),
        problem_link=problem_link.strip(),
        difficulty=difficulty.strip() if difficulty else None,
        rating=parse_int(rating),
        description=description,
        github_solution_link=github_solution_link.strip() if github_solution_link else None,
        hindi_solution_link=hindi_solution_link.strip() if hindi_solution_link else None,
        english_solution_link=english_solution_link.strip() if english_solution_link else None,
        created_by=parse_int(created_by),
        is_premium=bool(is_premium),
        created_at=datetime.utcnow(),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {
        "id": item.id,
        "title": item.title,
        "problem_link": item.problem_link,
        "difficulty": item.difficulty,
        "rating": item.rating,
        # "description": item.description,
        "github_solution_link": item.github_solution_link,
        "hindi_solution_link": item.hindi_solution_link,
        "english_solution_link": item.english_solution_link,
        "created_by": item.created_by,
        "is_premium": item.is_premium,
        "created_at": item.created_at,
    }


@router.get("/problems")
def list_problems(db: Session = Depends(get_db)):
    items = db.query(CP51Problem).all()
    return [
        {
            "id": i.id,
            "title": i.title,
            "problem_link": i.problem_link,
            "difficulty": i.difficulty,
            "rating": i.rating,
            # "description": i.description,
            "github_solution_link": i.github_solution_link,
            "hindi_solution_link": i.hindi_solution_link,
            "english_solution_link": i.english_solution_link,
            "created_by": i.created_by,
            "is_premium": i.is_premium,
            "created_at": i.created_at,
        }
        for i in items
    ]


# GET by id
@router.get("/problems/{problem_id}")
def get_problem(problem_id: int, db: Session = Depends(get_db)):
    item = db.query(CP51Problem).filter(CP51Problem.id == problem_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Problem not found")
    return {
        "id": item.id,
        "title": item.title,
        "problem_link": item.problem_link,
        "difficulty": item.difficulty,
        "rating": item.rating,
        "description": item.description,
        "github_solution_link": item.github_solution_link,
        "hindi_solution_link": item.hindi_solution_link,
        "english_solution_link": item.english_solution_link,
        "created_by": item.created_by,
        "is_premium": item.is_premium,
        "created_at": item.created_at,
    }

# UPDATE (PUT form - full update)
@router.put("/problems/{problem_id}")
def update_problem_full(
    problem_id: int,
    title: str = Form(..., max_length=255),
    problem_link: str = Form(..., max_length=500),
    difficulty: Optional[str] = Form(None, max_length=50),
    rating: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    github_solution_link: Optional[str] = Form(None, max_length=500),
    hindi_solution_link: Optional[str] = Form(None, max_length=500),
    english_solution_link: Optional[str] = Form(None, max_length=500),
    is_premium: Optional[bool] = Form(False),
    db: Session = Depends(get_db),
):
    item = db.query(CP51Problem).filter(CP51Problem.id == problem_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Problem not found")

    item.title = title.strip()
    item.problem_link = problem_link.strip()
    item.difficulty = difficulty.strip() if difficulty else None
    item.rating = parse_int(rating)
    item.description = description
    item.github_solution_link = github_solution_link.strip() if github_solution_link else None
    item.hindi_solution_link = hindi_solution_link.strip() if hindi_solution_link else None
    item.english_solution_link = english_solution_link.strip() if english_solution_link else None
    item.is_premium = bool(is_premium)

    db.commit()
    db.refresh(item)
    return {
        "id": item.id,
        "title": item.title,
        "problem_link": item.problem_link,
        "difficulty": item.difficulty,
        "rating": item.rating,
        "description": item.description,
        "github_solution_link": item.github_solution_link,
        "hindi_solution_link": item.hindi_solution_link,
        "english_solution_link": item.english_solution_link,
        "created_by": item.created_by,
        "is_premium": item.is_premium,
        "created_at": item.created_at,
    }

# UPDATE (PATCH form - partial update)
@router.patch("/problems/{problem_id}")
def update_problem_partial(
    problem_id: int,
    title: Optional[str] = Form(None),
    problem_link: Optional[str] = Form(None),
    difficulty: Optional[str] = Form(None),
    rating: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    github_solution_link: Optional[str] = Form(None),
    hindi_solution_link: Optional[str] = Form(None),
    english_solution_link: Optional[str] = Form(None),
    is_premium: Optional[bool] = Form(None),
    db: Session = Depends(get_db),
):
    item = db.query(CP51Problem).filter(CP51Problem.id == problem_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Problem not found")

    if title is not None:
        item.title = title.strip()
    if problem_link is not None:
        item.problem_link = problem_link.strip()
    if difficulty is not None:
        item.difficulty = difficulty.strip() if difficulty else None
    if rating is not None:
        item.rating = parse_int(rating)
    if description is not None:
        item.description = description
    if github_solution_link is not None:
        item.github_solution_link = github_solution_link.strip() if github_solution_link else None
    if hindi_solution_link is not None:
        item.hindi_solution_link = hindi_solution_link.strip() if hindi_solution_link else None
    if english_solution_link is not None:
        item.english_solution_link = english_solution_link.strip() if english_solution_link else None
    if is_premium is not None:
        item.is_premium = bool(is_premium)

    db.commit()
    db.refresh(item)
    return {
        "id": item.id,
        "title": item.title,
        "problem_link": item.problem_link,
        "difficulty": item.difficulty,
        "rating": item.rating,
        "description": item.description,
        "github_solution_link": item.github_solution_link,
        "hindi_solution_link": item.hindi_solution_link,
        "english_solution_link": item.english_solution_link,
        "created_by": item.created_by,
        "is_premium": item.is_premium,
        "created_at": item.created_at,
    }

# DELETE
@router.delete("/problems/{problem_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_problem(problem_id: int, db: Session = Depends(get_db)):
    item = db.query(CP51Problem).filter(CP51Problem.id == problem_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Problem not found")
    db.delete(item)
    db.commit()
    return None
