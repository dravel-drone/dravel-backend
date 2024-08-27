from database.mariadb_session import SessionLocal
from models import Refresh
from datetime import datetime


async def delete_expired_refresh():
    db = SessionLocal()
    try:
        expired_refresh = db.query(Refresh).filter(
            Refresh.expired_date < datetime.utcnow()
        ).all()
        for r in expired_refresh:
            db.delete(r)
        db.commit()
        print(f"{len(expired_refresh)} refresh tokens deleted")
    finally:
        db.close()
