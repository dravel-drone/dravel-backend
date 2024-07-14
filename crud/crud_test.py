from sqlalchemy.orm import Session
import models

def get_test_user(db: Session):
    return db.query(models.User).filter(models.User.uid == 'suo39jdosHUI8').first()
