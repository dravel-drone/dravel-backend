import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from core.security import create_refresh_token, get_password_hash
from core.config import settings
from database.mariadb_session import get_db
from models import User as UserModel
from schemas import UserCreate, User

router = APIRouter()


@router.post("/register", response_model=User, status_code=200)
def create_term(
        user: UserCreate,
        db: Session = Depends(get_db)
):
    # 아이디 중복 검사
    existing_id = db.query(UserModel).filter(UserModel.id == user.id).first()
    if existing_id:
        raise HTTPException(status_code=400, detail="이미 있는 아이디입니다.")

    hashed_password = get_password_hash(user.password)
    user.password = hashed_password

    token_data = {
        "sub": str(UserModel.uid),
        "level": 0
    }
    expires_delta = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    refresh_token, expire = create_refresh_token(token_data, expires_delta)

    db_user = UserModel(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
