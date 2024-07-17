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

