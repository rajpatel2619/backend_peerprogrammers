from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from ...models.codeforces_ladder_model import (
    Ladder, LadderProblem, UserProblemStatus
)
from ...models.user_model import User
from sqlalchemy import func

from ...connection.utility import get_db

router = APIRouter(prefix="/ladders", tags=["Ladders"])

# ✅ Fetch all ladders metadata
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


# ✅ Fetch problems in a ladder (optional limit for pagination)
@router.get("/{ladder_id}/problems", summary="Get problems in a ladder")
def get_ladder_problems(
    ladder_id: int,
    limit: int = Query(None, description="Optional limit for pagination"),
    db: Session = Depends(get_db)
):
    ladder = db.query(Ladder).filter(Ladder.id == ladder_id).first()
    if not ladder:
        raise HTTPException(status_code=404, detail="Ladder not found")

    query = (
        db.query(LadderProblem)
        .filter(LadderProblem.ladder_id == ladder_id)
        .order_by(LadderProblem.problem_order)
    )
    if limit:
        query = query.limit(limit)
    problems = query.all()

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


# ✅ Mark problem for revisit
@router.post("/problems/{problem_id}/user/{user_id}/revisit", summary="Mark problem for revisit")
def mark_problem_revisit(problem_id: int, user_id: int, db: Session = Depends(get_db)):
    # Ensure problem exists
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
        status.is_revisit = not status.is_revisit  # Toggle revisit flag
        status.checked_at = datetime.utcnow()

    db.commit()
    return {"message": f"Problem revisit status updated to {status.is_revisit}"}


# ✅ Update solve status
@router.post("/problems/{problem_id}/status", summary="Mark problem solved/unsolved for a user")
def update_problem_status(
    problem_id: int,
    user_id: int = Query(...),
    is_completed: bool = Query(...),
    db: Session = Depends(get_db)
):
    problem = db.query(LadderProblem).filter(LadderProblem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    status = (
        db.query(UserProblemStatus)
        .filter(UserProblemStatus.problem_id == problem_id, UserProblemStatus.user_id == user_id)
        .first()
    )

    if status:
        status.is_completed = is_completed
        status.checked_at = datetime.utcnow()
    else:
        status = UserProblemStatus(
            user_id=user_id,
            problem_id=problem_id,
            is_completed=is_completed,
            checked_at=datetime.utcnow()
        )
        db.add(status)

    db.commit()
    return {"message": f"Problem marked as {'completed' if is_completed else 'not completed'}"}


# ✅ Missing route — Get completed problems for a user in a ladder
@router.get("/{ladder_id}/user/{user_id}/completed", summary="Fetch completed problems for a user")
def get_completed_problems(ladder_id: int, user_id: int, db: Session = Depends(get_db)):
    problems = (
        db.query(UserProblemStatus.problem_id)
        .join(LadderProblem, UserProblemStatus.problem_id == LadderProblem.id)
        .filter(
            LadderProblem.ladder_id == ladder_id,
            UserProblemStatus.user_id == user_id,
            UserProblemStatus.is_completed == True
        )
        .all()
    )
    return [{"id": pid} for (pid,) in problems]


# ✅ Extra route — Fetch revisited problems for a user
@router.get("/{ladder_id}/user/{user_id}/revisited", summary="Fetch revisited problems for a user")
def get_revisited_problems(ladder_id: int, user_id: int, db: Session = Depends(get_db)):
    problems = (
        db.query(UserProblemStatus.problem_id)
        .join(LadderProblem, UserProblemStatus.problem_id == LadderProblem.id)
        .filter(
            LadderProblem.ladder_id == ladder_id,
            UserProblemStatus.user_id == user_id,
            UserProblemStatus.is_revisit == True
        )
        .all()
    )
    return [{"id": pid} for (pid,) in problems]



@router.get("/cp51/leaderboard", summary="Get CP51 Leaderboard")
def get_cp51_leaderboard(db: Session = Depends(get_db)):
    # 1️⃣ Total problems across all ladders
    total_problems = db.query(func.count(LadderProblem.id)).scalar() or 0

    # 2️⃣ User solved counts (only completed problems)
    solved_counts = (
        db.query(UserProblemStatus.user_id, func.count(UserProblemStatus.problem_id).label("solved_count"))
        .filter(UserProblemStatus.is_completed == True)
        .group_by(UserProblemStatus.user_id)
        .all()
    )

    # Convert to dict for quick lookup
    solved_dict = {user_id: solved_count for user_id, solved_count in solved_counts}

    # 3️⃣ Get all users who have solved something
    user_ids = list(solved_dict.keys())
    users = db.query(User).all()

    leaderboard = []
    for u in users:
        solved = solved_dict.get(u.id, 0)
        progress_pct = (solved / total_problems * 100) if total_problems else 0

        # Assign rank title + emoji based on thresholds
        if progress_pct >= 40:
            title = "🏆 Conqueror"
        elif progress_pct >= 30:
            title = "🎯 Ace"
        elif progress_pct >= 20:
            title = "👑 Crown"
        elif progress_pct >= 10:
            title = "💎 Diamond"
        elif progress_pct >= 8:
            title = "🔘 Platinum"
        elif progress_pct >= 5:
            title = "🥇 Gold"
        else:
            title = "🥈 Silver"

        leaderboard.append({
            "user": u.username,
            "problems_solved": solved,
            "progress": f"{round(progress_pct)}% of total",
            "title": title
        })

    # 4️⃣ Sort by problems solved (descending) and assign rank
    leaderboard.sort(key=lambda x: x["problems_solved"], reverse=True)
    for idx, entry in enumerate(leaderboard, start=1):
        entry["rank"] = idx

    # 5️⃣ Total users & average solved
    total_users = len(leaderboard)
    avg_solved = round(sum(e["problems_solved"] for e in leaderboard) / total_users) if total_users else 0

    return {
        "total_users": total_users,
        "total_problems": total_problems,
        "average_solved": avg_solved,
        "leaderboard": leaderboard
    }



@router.get("/cp51/leaderboard/user/{user_id}/rank", summary="Get a user's rank on the CP51 leaderboard")
def get_user_rank(user_id: int, db: Session = Depends(get_db)):
    # 1. Get total problems in all ladders
    total_problems = db.query(func.count(LadderProblem.id)).scalar() or 0

    # 2. Fetch solved counts for all users who solved any problem
    solved_counts = (
        db.query(UserProblemStatus.user_id, func.count(UserProblemStatus.problem_id).label("solved_count"))
        .filter(UserProblemStatus.is_completed == True)
        .group_by(UserProblemStatus.user_id)
        .order_by(func.count(UserProblemStatus.problem_id).desc())
        .all()
    )
    
    # 3. Map user_id to solved_count and rank users
    user_rank = None
    current_rank = 0
    prev_count = None
    rank_offset = 0  # for handling ties

    for i, (u_id, solved_count) in enumerate(solved_counts, start=1):
        # Handle ties in ranking
        if solved_count != prev_count:
            current_rank = i
            rank_offset = 0
        else:
            rank_offset += 1

        if u_id == user_id:
            user_rank = current_rank
            user_solved = solved_count
            break
        prev_count = solved_count

    if user_rank is None:
        # User has no solved problems or does not exist in leaderboard
        # Check if user exists
        user_exists = db.query(User).filter(User.id == user_id).first()
        if not user_exists:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "user_id": user_id,
            "rank": None,
            "problems_solved": 0,
            "progress": "0% of total problems"
        }

    progress_pct = (user_solved / total_problems * 100) if total_problems else 0
    return {
        "user_id": user_id,
        "rank": user_rank,
        "problems_solved": user_solved,
        "progress": f"{round(progress_pct)}% of total problems"
    }