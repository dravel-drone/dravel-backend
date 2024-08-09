from datetime import datetime
from typing import Dict, Any
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status
import models
from core.security import decode_refresh_token, create_access_token
from database.mariadb_session import get_db


def update_access_token(refresh_token: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    try:
        payload = decode_refresh_token(refresh_token)
        uid = payload["sub"]
        is_admin = payload.get("class")

        db_token = db.query(models.Refresh).filter(
            models.Refresh.token == refresh_token,
            models.Refresh.uid == str(uid)
        ).first()

        if db_token is None or db_token.expired_date < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_data = {"sub": uid, "class": is_admin}
        access_token, access_token_expire = create_access_token(data=access_token_data)

        return {
            "access_token": access_token,
            "access_token_expire": access_token_expire
        }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )