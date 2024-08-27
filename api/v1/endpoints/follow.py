from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database.mariadb_session import get_db

from models import User

from typing import Dict, Any
from core.auth import verify_user_token

router = APIRouter()

@router.post("/follow/{target_uid}")
async def refresh_access_token(
        target_uid: str,
        request: Request,
        user_data: Dict[str, Any] = Depends(verify_user_token),
        db: Session = Depends(get_db)
):
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="로그인한 유저만 사용 가능합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    uid = user_data["sub"]
    user = db.query(User).filter(
        User.uid == uid
    ).first()
    target_user = db.query(User).filter(
        User.uid == target_uid
    ).first()
    if user is None or target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="존재하지 않는 사용자입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )


