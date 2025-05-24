
# ✅ Ensure this import registers all models BEFORE create_all
from fastapi import FastAPI
from .database import engine, Base
from . import models
from .models import  User, Course, CourseDetails, CourseAuthor, UserDetails, UserSocialDetails
from .routers import  login, signup, course
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

print("Creating tables if they don't exist...")
print("Tables known to Base.metadata:", Base.metadata.tables.keys())
print(dir(models))  # Should list your model classes like Course
print(models.Course)  # Should print the class, not an error
Base.metadata.create_all(bind=engine)
print("Table creation done.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(login.router)
app.include_router(signup.router)
app.include_router(course.router)

# @app.on_event("startup")
# def create_tables():
#     Base.metadata.create_all(bind=engine)
