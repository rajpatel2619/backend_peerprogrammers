from fastapi import APIRouter, Depends, HTTPException, Query, Form, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, update
from datetime import datetime
import requests
import re

from ...models.codeforces_ladder_model import (
    Ladder, LadderProblem, UserProblemStatus, UserCPProfile
)
from ...models.user_model import User
from ...connection.utility import get_db

router = APIRouter(prefix="/ladders", tags=["Ladders"])

def fetch_solved_from_codeforces(handle: str):
    url = f"https://codeforces.com/api/user.status?handle={handle}"
    r = requests.get(url)
    data = r.json()
    if data.get("status") != "OK":
        raise HTTPException(status_code=400, detail=f"Codeforces API error: {data.get('comment')}")
    solved_set = set()
    for sub in data["result"]:
        if sub.get("verdict") == "OK":
            prob = sub["problem"]
            key = f"{prob.get('contestId', '')}{prob.get('index', '')}"
            solved_set.add(key)
    return solved_set

# ✅ Fetch all ladders metadata (no problem limit needed)
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

# ✅ Fetch problems in a ladder (limit to 10 ALWAYS)
@router.get("/{ladder_id}/problems", summary="Get problems in a ladder")
def get_ladder_problems(
    ladder_id: int,
    limit: int = Query(None, description="Optional limit for pagination"),  # Limit param kept for compatibility
    db: Session = Depends(get_db)
):
    ladder = db.query(Ladder).filter(Ladder.id == ladder_id).first()
    if not ladder:
        raise HTTPException(status_code=404, detail="Ladder not found")

    # Always apply limit=10, ignore client, or use lesser of [client limit, 10]
    use_limit = min(limit or 10, 10)
    problems = (
        db.query(LadderProblem)
        .filter(LadderProblem.ladder_id == ladder_id)
        .order_by(LadderProblem.problem_order)
        .limit(use_limit)
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

# ✅ Mark problem for revisit
@router.post("/problems/{problem_id}/user/{user_id}/revisit", summary="Mark problem for revisit")
def mark_problem_revisit(problem_id: int, user_id: int, db: Session = Depends(get_db)):
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
        status.is_revisit = not status.is_revisit
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

# ✅ Get completed problems for a user in a ladder (limit to 10)
@router.get("/{ladder_id}/user/{user_id}/completed", summary="Fetch completed problems for a user")
def get_completed_problems(ladder_id: int, user_id: int, db: Session = Depends(get_db)):
    cp_profile = db.query(UserCPProfile).filter(UserCPProfile.user_id == user_id).first()
    if cp_profile and cp_profile.codeforces_handle:
        solved_set = fetch_solved_from_codeforces(cp_profile.codeforces_handle)
        ladder_problems = (
            db.query(LadderProblem.id, LadderProblem.problem_url)
            .filter(LadderProblem.ladder_id == ladder_id)
            .limit(50) # (fetch up to 50 to have margin, will slice to 10 after check)
            .all()
        )
        completed_ids = []
        for pid, url in ladder_problems:
            match = re.search(r"(?:/contest/|/problemset/problem/)(\d+)/([A-Z]\d*)", url)
            if match:
                contest_id, index = match.groups()
                if f"{contest_id}{index}" in solved_set:
                    completed_ids.append({"id": pid})
            if len(completed_ids) >= 10:
                break
        return completed_ids
    else:
        problems = (
            db.query(UserProblemStatus.problem_id)
            .join(LadderProblem, UserProblemStatus.problem_id == LadderProblem.id)
            .filter(
                LadderProblem.ladder_id == ladder_id,
                UserProblemStatus.user_id == user_id,
                UserProblemStatus.is_completed == True
            )
            .limit(10)
            .all()
        )
        return [{"id": pid} for (pid,) in problems]

# ✅ Fetch revisited problems for a user (limit to 10)
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
        .limit(10)
        .all()
    )
    return [{"id": pid} for (pid,) in problems]

@router.get("/cp51/leaderboard", summary="Get CP51 Leaderboard")
def get_cp51_leaderboard(db: Session = Depends(get_db)):
    total_problems = db.query(func.count(LadderProblem.id)).scalar() or 0
    solved_counts = (
        db.query(UserProblemStatus.user_id, func.count(UserProblemStatus.problem_id).label("solved_count"))
        .filter(UserProblemStatus.is_completed == True)
        .group_by(UserProblemStatus.user_id)
        .all()
    )
    solved_dict = {user_id: solved_count for user_id, solved_count in solved_counts}
    user_ids = list(solved_dict.keys())
    users = db.query(User).all()
    leaderboard = []
    for u in users:
        solved = solved_dict.get(u.id, 0)
        progress_pct = (solved / total_problems * 100) if total_problems else 0
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
    leaderboard.sort(key=lambda x: x["problems_solved"], reverse=True)
    for idx, entry in enumerate(leaderboard, start=1):
        entry["rank"] = idx
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
    total_problems = db.query(func.count(LadderProblem.id)).scalar() or 0
    solved_counts = (
        db.query(UserProblemStatus.user_id, func.count(UserProblemStatus.problem_id).label("solved_count"))
        .filter(UserProblemStatus.is_completed == True)
        .group_by(UserProblemStatus.user_id)
        .order_by(func.count(UserProblemStatus.problem_id).desc())
        .all()
    )
    user_rank = None
    current_rank = 0
    prev_count = None
    rank_offset = 0
    for i, (u_id, solved_count) in enumerate(solved_counts, start=1):
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

@router.post("/profile", summary="Create or update a user's CP profile")
def set_cp_profile(
    user_id: int = Form(...),
    codeforces_handle: str = Form(None),
    atcoder_handle: str = Form(None),
    leetcode_handle: str = Form(None),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    cp_profile = db.query(UserCPProfile).filter(UserCPProfile.user_id == user_id).first()
    if not cp_profile:
        cp_profile = UserCPProfile(user_id=user_id)
    if codeforces_handle is not None:
        cp_profile.codeforces_handle = codeforces_handle.strip()
    if atcoder_handle is not None:
        cp_profile.atcoder_handle = atcoder_handle.strip()
    if leetcode_handle is not None:
        cp_profile.leetcode_handle = leetcode_handle.strip()
    cp_profile.last_synced_at = datetime.utcnow()
    db.add(cp_profile)
    db.commit()
    db.refresh(cp_profile)
    return {
        "message": "CP profile updated successfully",
        "data": {
            "user_id": cp_profile.user_id,
            "codeforces_handle": cp_profile.codeforces_handle,
            "atcoder_handle": cp_profile.atcoder_handle,
            "leetcode_handle": cp_profile.leetcode_handle
        }
    }

@router.get("/profile/{user_id}", summary="Get username, CP profile, and overall progress")
def get_cp_profile(user_id: int, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Total problems in the system
    total_count = db.query(LadderProblem).count()

    # Solved problems for this user
    solved_count = (
        db.query(UserProblemStatus)
        .filter(
            UserProblemStatus.user_id == user_id,
            UserProblemStatus.is_completed.is_(True)
        )
        .count()
    )

    return {
        "user_id": user.id,
        "username": user.username,
        "codeforces_handle": user.cp_profile.codeforces_handle if user.cp_profile else None,
        "atcoder_handle": user.cp_profile.atcoder_handle if user.cp_profile else None,
        "leetcode_handle": user.cp_profile.leetcode_handle if user.cp_profile else None,
        "overall_progress": {
            "solved": solved_count,
            "total": total_count
        }
    }



@router.post("/codeforces/sync", summary="Sync solved problems from Codeforces for a specific ladder")
async def sync_codeforces_problems_for_ladder(
    request: Request,
    db: Session = Depends(get_db)
):
    data = await request.json()
    user_id = data.get("user_id")
    ladder_id = data.get("ladder_id")
    if not user_id or not ladder_id:
        raise HTTPException(status_code=400, detail="Missing user_id or ladder_id")
    cp_profile = db.query(UserCPProfile).filter(UserCPProfile.user_id == user_id).first()
    if not cp_profile or not cp_profile.codeforces_handle:
        raise HTTPException(status_code=400, detail="No Codeforces handle found for this user")
    solved_set = fetch_solved_from_codeforces(cp_profile.codeforces_handle)
    ladder_problems = (
        db.query(LadderProblem.id, LadderProblem.problem_url)
        .filter(LadderProblem.ladder_id == ladder_id, LadderProblem.online_judge == "Codeforces")
        .all()
    )
    now = datetime.utcnow()
    problem_ids_to_update = []
    problem_status_new = []
    for pid, url in ladder_problems:
        match = re.search(r"(?:/contest/|/problemset/problem/)(\d+)/([A-Z]\d*)", url)
        if match:
            contest_id, index = match.groups()
            if f"{contest_id}{index}" in solved_set:
                existing_status = (
                    db.query(UserProblemStatus)
                    .filter(UserProblemStatus.problem_id == pid, UserProblemStatus.user_id == user_id)
                    .first()
                )
                if existing_status:
                    if not existing_status.is_completed:
                        problem_ids_to_update.append(pid)
                else:
                    problem_status_new.append(UserProblemStatus(
                        user_id=user_id,
                        problem_id=pid,
                        is_completed=True,
                        checked_at=now
                    ))
    if problem_status_new:
        db.bulk_save_objects(problem_status_new)
    if problem_ids_to_update:
        db.execute(
            update(UserProblemStatus)
            .where(UserProblemStatus.problem_id.in_(problem_ids_to_update))
            .where(UserProblemStatus.user_id == user_id)
            .values(is_completed=True, checked_at=now)
        )
    cp_profile.last_synced_at = now
    db.commit()
    return {
        "message": f"Synced {len(problem_status_new) + len(problem_ids_to_update)} problems from Codeforces for ladder {ladder_id}",
        "last_synced_at": now.isoformat()
    }
