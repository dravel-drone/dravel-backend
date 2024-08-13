from typing import Dict, Any, List

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
        term_data: TermCreate,
        db: Session = Depends(get_db),
        user_data: Dict[str, Any] = Depends(verify_user_token)
):
    if not user_data.get("level"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db_term = TermModel(**term_data.dict())
    db.add(db_term)
    db.commit()
    db.refresh(db_term)

    return db_term

@router.get("/term", response_model=List[Term], status_code=200)
def get_all_terms(db: Session = Depends(get_db)):
    terms = db.query(TermModel).all()
    if not terms:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested resource was not found."
        )
    return terms

@router.get("/term/{term_id}", response_model=Term, status_code=200)
def get_term_by_id(term_id: int, db: Session = Depends(get_db)):
    term = db.query(TermModel).filter(TermModel.id == term_id).first()
    if not term:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested resource was not found."
        )
    return term


@router.patch("/term/{term_id}", response_model=Term, status_code=200)
def update_term(
        term_id: int,
        term_data: TermCreate,
        db: Session = Depends(get_db),
        user_data: Dict[str, Any] = Depends(verify_user_token)
):
    if not user_data.get("level"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    term = db.query(TermModel).filter(TermModel.id == term_id).first()
    if not term:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested resource was not found."
        )

    for key, value in term_data.dict(exclude_unset=True).items():
        setattr(term, key, value)
    db.commit()
    db.refresh(term)

    return term


@router.delete("/term/{term_id}", status_code=204)
def delete_term(
        term_id: int,
        db: Session = Depends(get_db),
        user_data: Dict[str, Any] = Depends(verify_user_token)
):
    if not user_data.get("level"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    term = db.query(TermModel).filter(TermModel.id == term_id).first()
    if not term:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested resource was not found."
        )

    db.delete(term)
    db.commit()

    return {"detail": "Term deleted successfully"}