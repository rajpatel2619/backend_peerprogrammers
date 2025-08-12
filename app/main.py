from app.routers.contact_us import contact_us
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime
from types import SimpleNamespace
from pathlib import Path
from dotenv import load_dotenv
import os

# ✅ Load environment variables from .env
load_dotenv()

# ✅ Determine base directory (cross-platform)
BASE_DIR = Path(__file__).resolve().parent

# ✅ Get UPLOAD_DIR from environment or default to ./uploads
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", BASE_DIR / "uploads"))

# ✅ Ensure the upload directory exists
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ✅ Create FastAPI app
app = FastAPI()

# ✅ Mount static file route for uploaded files
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ✅ Import routers and models
from .routers.users import login, signup, user
from .routers.courses import student_courses, teacher_courses, course, domains
from .routers.resources import resources
from .connection.database import engine, Base
from .models.testing_mode import *
from .models.user_model import User, TempUser, UserDetails, UserSocialDetails
from .models.course_model import *
from .models.resource_model import *
from .models.registration_model import *
from .routers.registration import registraion
from .models.registration_model import CourseRegistration
from .models.registration_model import Payment
from .models.problem_model import (
    CodingProblem, Tag, Company,
    ProblemTag, ProblemCompany, Sheet,
    SheetProblem, Favorite
)
from .routers.problems import problems
from .routers.codeforces_ladder import codeforces_ladder
from .models.codeforces_ladder_model import *
from .routers.contact_us import *
from .models.contact_us_model import *




# ✅ Create tables


# Base.metadata.create_all(bind=engine, tables=[
#     Payment.__table__,
# #     CourseRegistration.__table__,
# # ])
# Drop association and referencing tables first
# ProblemTag.__table__.drop(engine, checkfirst=True)
# ProblemCompany.__table__.drop(engine, checkfirst=True)
# SheetProblem.__table__.drop(engine, checkfirst=True)
# Favorite.__table__.drop(engine, checkfirst=True)

# # Then drop main tables
# CodingProblem.__table__.drop(engine, checkfirst=True)
# Tag.__table__.drop(engine, checkfirst=True)
# Company.__table__.drop(engine, checkfirst=True)
# Sheet.__table__.drop(engine, checkfirst=True)
#

Base.metadata.create_all(bind=engine)
# Base.metadata.drop_all(bind=engine)

# CourseDomain.__table__.drop(engine)
# DomainTag.__table__.drop(engine)

# LadderProblemSolution.__table__.drop(engine, checkfirst=True)
# UserProblemStatus.__table__.drop(engine, checkfirst=True)
# LadderProblem.__table__.drop(engine, checkfirst=True)
# Ladder.__table__.drop(engine, checkfirst=True)

# CourseMentor.__table__.drop(engine, checkfirst=True)


# ✅ CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with specific origin(s) in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Register routers
app.include_router(login.router)
app.include_router(signup.router)
app.include_router(student_courses.router)
app.include_router(teacher_courses.router)
app.include_router(user.router)
app.include_router(resources.router)
app.include_router(registraion.router)
app.include_router(course.router)
app.include_router(domains.router)
app.include_router(problems.router)
app.include_router(codeforces_ladder.router)
app.include_router(contact_us.router)



# ✅ Optional: DB testing code (commented out)
# with Session(bind=engine) as session:
#     new_user = User(
#         username="new_username",
#         password="hashed_password",
#         createdAt=datetime.utcnow(),
#         updatedAt=datetime.utcnow(),
#         active=True
#     )
#     session.add(new_user)
#     session.commit()
#     print(f"Inserted user with ID: {new_user.id}")
