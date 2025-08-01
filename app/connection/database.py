from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL-encoded password: @ → %40
DATABASE_URL = "mysql+pymysql://u613289423_pprogrammers:Peerprogrammers%403214@srv1910.hstgr.io:3306/u613289423_pprogrammers"


# DATABASE_URL = "mysql+pymysql://u613289423_peer_dev:Peer%40programmers%403214@srv1910.hstgr.io:3306/u613289423_peer_dev"

engine = create_engine(DATABASE_URL, echo=True,future=True, pool_pre_ping=True, pool_recycle=280)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
