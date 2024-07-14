from typing import Generator
from database.mariadb_session import SessionLocal

def get_mariadb() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
