from datetime import datetime
from typing import Dict, Any
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from starlette import status
from core.security import decode_refresh_token, create_access_token, decode_access_token
from database.mariadb_session import get_db
from models import Refresh


def verify_user_token(Authorization: str = Header(...)) -> Dict[str, Any]:
    try:
        token = Authorization.split(" ")[1]
        payload = decode_access_token(token)
        uid = payload["sub"]
        is_admin = payload["level"]
        print(payload)
        if not uid or is_admin is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",)
        return {"sub": uid, "level": is_admin}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

def update_access_token(refresh_token: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    try:
        payload = decode_refresh_token(refresh_token)
        uid = payload["sub"]
        is_admin = payload["level"]

        if not uid or is_admin is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token")

        db_token = db.query(Refresh).filter(
            Refresh.token == refresh_token,
            Refresh.uid == str(uid)
        ).first()

        if db_token is None or db_token.expired_date < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_data = {"sub": uid, "level": is_admin}
        access_token, access_token_expire = create_access_token(data=access_token_data)

        return {
            "access_token": access_token,
            "access_token_expire": access_token_expire
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e