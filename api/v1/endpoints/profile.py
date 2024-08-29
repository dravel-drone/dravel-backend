from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends
from sqlalchemy import null
from sqlalchemy.orm import Session

from core.auth import verify_user_token
from database.mariadb_session import get_db
from models import (
    User as UserModel,
    Follow as FollowModel,
    Review as ReviewModel
)

from schemas import Profile

router = APIRouter()

@router.get("/profile/{uid}", response_model=Profile, status_code=200)
def get_user_profile(
    uid: str,
    db: Session = Depends(get_db),
    user: Optional[Dict[str, Any]] = Depends(verify_user_token)
):

    print(uid)
    db_user = db.query(UserModel).filter(UserModel.uid == uid).first()
    print(db_user)

    # 로그인 한 유저일 경우, 팔로우 여부 확인
    if user:
        if user['sub']==db_user.uid:
            is_following = null
        else:
            is_following = db.query(FollowModel).filter(
                FollowModel.follower_uid == user['sub'],
                FollowModel.following_uid == db_user.uid
            ).count()
    else:
        is_following = 0  # 로그인하지 않은 경우

    following_count = db.query(FollowModel).filter(FollowModel.follower_uid == db_user.uid).count()
    follower_count = db.query(FollowModel).filter(FollowModel.following_uid == db_user.uid).count()
    post_count = db.query(ReviewModel).filter(ReviewModel.writer_uid == db_user.uid).count()

    response = Profile(
        uid=db_user.uid,
        name=db_user.name,
        image=db_user.image,
        post_count=post_count,
        follower_count=follower_count,
        following_count=following_count,
        one_liner=db_user.one_liner,
        drone=db_user.drone,
        is_following=is_following
    )

    return response