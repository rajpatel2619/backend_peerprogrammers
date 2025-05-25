
# ✅ Ensure this import registers all models BEFORE create_all
from .routers.users import login
from .routers.courses import student_courses, teacher_courses
from fastapi import FastAPI
from .connection.database import engine, Base
from .routers.users import  signup
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

Base.metadata.create_all(bind=engine)

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