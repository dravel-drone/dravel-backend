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