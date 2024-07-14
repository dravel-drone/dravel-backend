from pydantic import BaseModel, EmailStr
from datetime import date

from typing import Optional

# pydantic 모델 추가

class UserTest(BaseModel):
    uid: str
    name: str
    is_admin: bool
    drone: Optional[str]

    class Config:
        orm_mode = True
