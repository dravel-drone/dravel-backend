from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from core.auth import update_access_token
from database.mariadb_session import get_db
from schemas import AccessTokenResponse, RefreshTokenRequest

from starlette.responses import Response

router = APIRouter()

@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_access_token(
        refresh_info: RefreshTokenRequest,
        request: Request,
        db: Session = Depends(get_db)
):
    refresh_token = request.cookies.get('refresh_token')
    try:
        token_data = update_access_token(refresh_token, refresh_info.device_id, db)
        response = Response()
        response.set_cookie(
            key="access_token",
            value=token_data['access_token'],
            httponly=True,
            secure=True,  # HTTPS 사용 시에만 secure 설정
            samesite="lax"  # SameSite 설정을 통해 CSRF 공격 방지
        )
        return response
    except HTTPException as e:
        raise e