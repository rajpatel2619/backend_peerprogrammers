from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL-encoded password: @ → %40
DATABASE_URL = "mysql+pymysql://u613289423_pprogrammers:Peerprogrammers%403214@srv1910.hstgr.io:3306/u613289423_pprogrammers"

# # Development
# DATABASE_URL = "mysql+pymysql://fastapi_dev_user:StrongDevPass%40123@77.37.44.8:3306/fastapi_development"

engine = create_engine(DATABASE_URL, echo=True,future=True, pool_pre_ping=True, pool_recycle=280)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()



# # Production
# DATABASE_URL = "mysql+pymysql://fastapi_prod_user:StrongProdPass%40123@@77.37.44.8:3306/fastapi_production"

# # Development
# DATABASE_URL = "mysql+pymysql://fastapi_dev_user:StrongDevPass%40123@@77.37.44.8:3306/fastapi_development"
