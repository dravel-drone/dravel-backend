from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from core.config import settings
from core.security import verify_password, create_refresh_token, create_access_token
from database.mariadb_session import get_db
from models import User as UserModel, Refresh as RefreshModel
from schemas import User, Login

router = APIRouter()


@router.post("/login", response_model=User, status_code=200)
def login(
        user: Login,
        db: Session = Depends(get_db)
):

    user_db = db.query(UserModel).filter(UserModel.id == user.id).first()
    if not user_db:
        raise HTTPException(status_code=400, detail="아이디 또는 비밀번호가 잘못 되었습니다. 아이디와 비밀번호를 정확히 입력해 주세요.")
    else:
        pw_verify = verify_password(user.password, user_db.password)
        if not pw_verify:
            raise HTTPException(status_code=400, detail="아이디 또는 비밀번호가 잘못 되었습니다. 아이디와 비밀번호를 정확히 입력해 주세요.")

        # 같은 아이디 로그인 시 기존 refresh 토큰 삭제
        existing_refresh_token = db.query(RefreshModel).filter(
            RefreshModel.uid == user_db.uid,
            RefreshModel.device_id == user.device_id
        ).first()
        if existing_refresh_token:
            db.delete(existing_refresh_token)
            db.commit()

        # access토큰 생성
        access_token_data = {
            "sub": user_db.uid,
            "level": user_db.is_admin
        }
        access_expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token, access_expire = create_access_token(access_token_data, access_expires_delta)
        #print(access_token)
        # refresh토큰 생성
        refresh_token_data = {
            "sub": user_db.uid,
            "level": user_db.is_admin
        }
        refresh_expires_delta = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        refresh_token, refresh_expire = create_refresh_token(refresh_token_data, refresh_expires_delta)
        db_refresh = RefreshModel(
            uid=user_db.uid, device_id=user.device_id, token=refresh_token, expired_date=refresh_expire)
        db.add(db_refresh)
        db.commit()
        #print(refresh_token)
        # HTTP-only 쿠키 설정
        response = JSONResponse(content={
            "uid": user_db.uid,
            "name": user_db.name,
            "id": user_db.id,
            "email": user_db.email,
            "age": user_db.age,
            "drone": user_db.drone,
        })
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,  # HTTPS 사용 시에만 secure 설정
            samesite="lax"  # SameSite 설정을 통해 CSRF 공격 방지
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,  # HTTPS 사용 시에만 secure 설정
            samesite="strict"  # refresh_token은 더 엄격한 SameSite 설정 사용
        )
    return response
