import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config
from models import Base

# SQLAlchemy Engine
engine = create_engine(
    f"sqlite:///{config.DB_PATH}", connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
