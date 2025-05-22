from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL-encoded password: @ → %40
DATABASE_URL = "mysql+pymysql://u613289423_pprogrammers:Peerprogrammers%403214@srv1910.hstgr.io:3306/u613289423_pprogrammers"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
