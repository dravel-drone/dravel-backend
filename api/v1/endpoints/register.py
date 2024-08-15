from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.security import get_password_hash
from database.mariadb_session import get_db
from models import User as UserModel, Term as TermModel, UserTermAgree as UserTermAgreeModel
from schemas import User, Register

router = APIRouter()


@router.post("/register", response_model=User, status_code=200)
def register(
        user: Register,
        agreed_term_ids: list[int],
        db: Session = Depends(get_db)
):
    # 약관 동의 여부 체크
    required_terms = db.query(TermModel).filter(TermModel.require == 1).all()
    required_term_ids = {term.id for term in required_terms}

    if not required_term_ids.issubset(set(agreed_term_ids)):
        raise HTTPException(status_code=400, detail="필수 약관에 동의하지 않았습니다.")

    # 아이디 중복 검사
    existing_id = db.query(UserModel).filter(UserModel.id == user.id).first()
    if existing_id:
        raise HTTPException(status_code=400, detail="이미 있는 아이디입니다.")

    hashed_password = get_password_hash(user.password)
    user.password = hashed_password

    db_user = UserModel(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    for term_id in agreed_term_ids:
        user_term_agree = UserTermAgreeModel(term_id=term_id, user_uid=db_user.uid)
        db.add(user_term_agree)
    db.commit()

    return db_user
