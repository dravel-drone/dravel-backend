from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from core.auth import verify_user_token
from database.mariadb_session import get_db
from models import Term as TermModel
from schemas import TermCreate, Term

router = APIRouter()

@router.post("/term", response_model=Term, status_code=201)
def create_term(
        term: TermCreate,
        db: Session = Depends(get_db),
        user_data: Dict[str, Any] = Depends(verify_user_token)
):
    if not user_data.get("level"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db_term = TermModel(**term.dict())
    db.add(db_term)
    db.commit()
    db.refresh(db_term)

    return db_term
