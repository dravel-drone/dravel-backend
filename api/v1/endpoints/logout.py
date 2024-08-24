from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_

from schemas import Logout
from starlette.responses import JSONResponse
from models import Refresh as RefreshModel

from core.security import decode_access_token

from database.mariadb_session import get_db

router = APIRouter()

@router.post("/logout")
async def logout(
        logout_info: Logout,
        request: Request,
        db: Session = Depends(get_db)
):
    existing_refresh_token = db.query(RefreshModel).filter(
        and_(
            RefreshModel.uid == logout_info.uid,
            RefreshModel.device_id == logout_info.device_id
        )
    ).first()

    if existing_refresh_token:
        db.delete(existing_refresh_token)
        db.commit()

    response = JSONResponse(content={"message": "로그아웃 되었습니다."})
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return response
