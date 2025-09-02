from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get DATABASE_URL from .env
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the .env file.")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    echo=True,
    future=True,
    pool_pre_ping=True,
    pool_recycle=280
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base model for ORM
Base = declarative_base()


# # Development
# DATABASE_URL = "mysql+pymysql://fastapi_dev_user:StrongDevPass%40123@@77.37.44.8:3306/fastapi_development"
# # Production
#DATABASE_URL = "mysql+pymysql://fastapi_prod_user:StrongProdPass%40123@77.37.44.8:3306/fastapi_production"
