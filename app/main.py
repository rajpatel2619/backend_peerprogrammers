from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import item
from .database import engine, Base

app = FastAPI()

Base.metadata.create_all(bind=engine)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(item.router)
