from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres:Arpitsuperbase*12@db.rsymeiwcuuuqfdexhzqz.supabase.co:5432/postgres"

engine = create_engine(DATABASE_URL, echo=True)  # echo=True helps debug SQL

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
