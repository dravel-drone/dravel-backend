from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from core.auth import verify_user_token
from database.mariadb_session import get_db
from models import (
    User as UserModel
)

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


@router.patch("/user/{user_id}", status_code=200)
def patch_user_info(
    user_id: str,
    name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    age: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    user: Optional[Dict[str, Any]] = Depends(verify_user_token)
):

    if user["level"] != 1:
        if user["sub"] != user_id:
            raise HTTPException(status_code=400, detail="본인이 아닙니다.")

    db_user = db.query(UserModel).filter(UserModel.uid == user_id).first()

    if name:
        db_user.name = name
    if email:
        db_user.email = email
    if age:
        db_user.age = age

    db.commit()
    db.refresh(db_user)

    response = JSONResponse(content={
        "uid": user_id,
        "name": db_user.name,
        "id": db_user.id,
        "email": db_user.email,
        "age": db_user.age,
        "drone": db_user.drone
    })

    return response

