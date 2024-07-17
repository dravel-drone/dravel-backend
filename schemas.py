from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# 약관(Term) pydantic 스키마
class TermBase(BaseModel):
    title: str
    content: str
    require: int
class TermCreate(TermBase):
    pass
class Term(TermBase):
    id: int
    class Config:
        orm_mode = True

# UserTermAgree pydantic 스키마
class UserTermAgreeBase(BaseModel):
    term_id: int
    user_uid: str
    created_at: datetime
class UserTermAgreeCreate(UserTermAgreeBase):
    pass
class UserTermAgree(UserTermAgreeBase):
    term: Term
    class Config:
        orm_mode = True

# User pydantic 스키마
class UserBase(BaseModel):
    name: str
    id: str
    email: str
    is_admin: int
    age: Optional[int]
    drone: Optional[str]
    image: Optional[str]
    one_liner: Optional[str]
class UserCreate(UserBase):
    pass
class User(UserBase):
    uid: str
    class Config:
        orm_mode = True
