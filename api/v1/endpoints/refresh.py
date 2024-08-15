from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.auth import update_access_token
from database.mariadb_session import get_db
from schemas import AccessTokenResponse, RefreshTokenRequest

router = APIRouter()

@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_access_token(
        request: RefreshTokenRequest,
        db: Session = Depends(get_db)
):
    try:
        token_data = update_access_token(request.refresh_token, db)
        return token_data
    except HTTPException as e:
        raise e