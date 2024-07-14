from fastapi import APIRouter, Depends
from schemas import UserTest

from sqlalchemy.orm import Session
from api.v1.depends import get_mariadb

import crud.crud_test as crud_test

router = APIRouter()

@router.get("")
async def root():
    return {"message": "Hello World"}


@router.get("/hello")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

@router.get("/test/user", response_model=UserTest)
async def get_test_user(db: Session = Depends(get_mariadb)):
    return crud_test.get_test_user(db)