from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from ...models.codeforces_ladder_model import (
    Ladder, LadderProblem, UserProblemStatus, LadderProblemSolution
)
from ...connection.utility import get_db

router = APIRouter(prefix="/ladders", tags=["Ladders"])

@router.get("/", summary="Fetch all ladders only (no problems)")
def get_all_ladders_meta(db: Session = Depends(get_db)):
    ladders = db.query(Ladder).all()
    return [
        {
            "id": ladder.id,
            "rating_range": ladder.rating_range,
            "lower_bound": ladder.lower_bound,
            "upper_bound": ladder.upper_bound,
            "problem_count": ladder.problem_count,
            "created_at": ladder.created_at.isoformat() if ladder.created_at else None
        }
        for ladder in ladders
    ]


@router.get("/{ladder_id}/problems", summary="Get all problems in a ladder")
def get_ladder_problems(ladder_id: int, db: Session = Depends(get_db)):
    ladder = db.query(Ladder).filter(Ladder.id == ladder_id).first()
    if not ladder:
        raise HTTPException(status_code=404, detail="Ladder not found")

    problems = (
        db.query(LadderProblem)
        .filter(LadderProblem.ladder_id == ladder_id)
        .order_by(LadderProblem.problem_order)
        .all()
    )

    return {
        "ladder": ladder.rating_range,
        "problems": [
            {
                "id": p.id,
                "problem_order": p.problem_order,
                "problem_name": p.problem_name,
                "problem_url": p.problem_url,
                "online_judge": p.online_judge,
                "difficulty": p.difficulty,
                "solutions": [
                    {"platform": s.platform, "link": s.link}
                    for s in p.solutions
                ]
            }
            for p in problems
        ]
    }


@router.get("/{ladder_id}/problems", summary="Get all problems in a ladder")
def get_ladder_problems(ladder_id: int, db: Session = Depends(get_db)):
    ladder = db.query(Ladder).filter(Ladder.id == ladder_id).first()
    if not ladder:
        raise HTTPException(status_code=404, detail="Ladder not found")

    problems = (
        db.query(LadderProblem)
        .filter(LadderProblem.ladder_id == ladder_id)
        .order_by(LadderProblem.problem_order)
        .all()
    )

    return {
        "ladder": ladder.rating_range,
        "problems": [
            {
                "id": p.id,
                "problem_order": p.problem_order,
                "problem_name": p.problem_name,
                "problem_url": p.problem_url,
                "online_judge": p.online_judge,
                "difficulty": p.difficulty,
                "solutions": [
                    {"platform": s.platform, "link": s.link}
                    for s in p.solutions
                ]
            }
            for p in problems
        ]
    }


@router.get("/{ladder_id}/user/{user_id}/completed", summary="Get completed problems by user")
def get_completed_problems(ladder_id: int, user_id: int, db: Session = Depends(get_db)):
    problems = (
        db.query(LadderProblem)
        .join(UserProblemStatus, LadderProblem.id == UserProblemStatus.problem_id)
        .filter(
            LadderProblem.ladder_id == ladder_id,
            UserProblemStatus.user_id == user_id,
            UserProblemStatus.is_completed.is_(True)
        )
        .order_by(LadderProblem.problem_order)
        .all()
    )

    return [
        {
            "id": p.id,
            "problem_order": p.problem_order,
            "problem_name": p.problem_name,
            "problem_url": p.problem_url,
            "online_judge": p.online_judge,
            "difficulty": p.difficulty,
            "solutions": [
                {"platform": s.platform, "link": s.link}
                for s in p.solutions
            ]
        }
        for p in problems
    ]


@router.post("/problems/{problem_id}/user/{user_id}/revisit", summary="Mark problem for revisit")
def mark_problem_revisit(problem_id: int, user_id: int, db: Session = Depends(get_db)):
    # Check if problem exists
    if not db.query(LadderProblem).filter(LadderProblem.id == problem_id).first():
        raise HTTPException(status_code=404, detail="Problem not found")

    status = (
        db.query(UserProblemStatus)
        .filter(UserProblemStatus.problem_id == problem_id, UserProblemStatus.user_id == user_id)
        .first()
    )

    if not status:
        status = UserProblemStatus(
            user_id=user_id,
            problem_id=problem_id,
            is_revisit=True,
            checked_at=datetime.utcnow()
        )
        db.add(status)
    else:
        status.is_revisit = True
        status.checked_at = datetime.utcnow()

    db.commit()
    return {"message": "Problem marked for revisit"}
