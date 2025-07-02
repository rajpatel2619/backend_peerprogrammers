
# ✅ Ensure this import registers all models BEFORE create_all
from .routers.users import login, user
from .routers.courses import student_courses, teacher_courses
from fastapi import FastAPI
from .connection.database import engine, Base
from .routers.users import  signup
from fastapi.middleware.cors import CORSMiddleware
from .models.testing_mode import *
from .models.user_model import User
from sqlalchemy.orm import Session
from datetime import datetime
from .routers.users.login import login_user
from types import SimpleNamespace
from .models.course_model import *

app = FastAPI()

# Base.metadata.create_all(bind=engine)

# Base.metadata.drop_all(
#     bind=engine,
#     tables=[
#         IndividualCourse.__table__,
#         CourseMentor.__table__,
#         CourseDomain.__table__
#     ]
# )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(login.router)
app.include_router(signup.router)
app.include_router(student_courses.router)
app.include_router(teacher_courses.router)
app.include_router(user.router)


# print("BEFORE____________________")
# # Create a new session to interact with the database
# with Session(bind=engine) as session:
#     users = session.query(User).all()
#     for user in users:
#         # Print user details, e.g., id, username, email
#         print(f"ID: {user.id}")


#         # Insert a new user into the database

# with Session(bind=engine) as session:
#     new_user = User(
#         username="new_username",
#         password="hashed_password",  # Replace with actual hashed password
#         createdAt=datetime.utcnow(),
#         updatedAt=datetime.utcnow(),
#         active=True
#     )
#     session.add(new_user)
#     session.commit()
#     print(f"Inserted user with ID: {new_user.id}")

# print("AFTER________________________")
# # Create a new session to interact with the database
# with Session(bind=engine) as session:
#     users = session.query(User).all()
#     for user in users:
#         # Print user details, e.g., id, username, email
#         print(f"ID: {user.id}")


# print("LOGIN_________________________")


# try:
#     with Session(bind=engine) as session:
#         # Create a mock payload object with email and password attributes
#         payload = SimpleNamespace(email="test@gmail.com", password="hello")
#         result = login_user(payload, db=session)
#         print(result)
# except Exception as e:
#     print("ERROR:", e)
#     import traceback
#     traceback.print_exc()

