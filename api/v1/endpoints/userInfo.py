from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.auth import verify_user_token
from database.mariadb_session import get_db
from models import (
    User as UserModel
)

from schemas import Profile

router = APIRouter()

@router.delete("/user/{user_id}", status_code=200)
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    user: Optional[Dict[str, Any]] = Depends(verify_user_token)
):

    if user["level"] != 1:
        if user["sub"] != user_id:
            raise HTTPException(status_code=400, detail="본인이 아닙니다.")

    db_user = db.query(UserModel).filter(UserModel.uid == user_id).first()
    db.delete(db_user)
    db.commit()

