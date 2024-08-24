from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from core.auth import update_access_token
from database.mariadb_session import get_db
from schemas import AccessTokenResponse, RefreshTokenRequest

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
        return token_data
    except HTTPException as e:
        raise e