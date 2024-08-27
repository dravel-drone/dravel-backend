from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database.mariadb_session import get_db

from models import User, Follow
from schemas import (
    User as UserSchema,
    Following as FollowingSchema,
)

from typing import Dict, Any, List
from core.auth import verify_user_token

router = APIRouter()

@router.post("/follow/{target_uid}", response_model=FollowingSchema, status_code=status.HTTP_200_OK)
async def following(
        target_uid: str,
        user_data: Dict[str, Any] = Depends(verify_user_token),
        db: Session = Depends(get_db)
):
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="로그인한 유저만 사용 가능합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    uid = user_data["sub"]
    user = db.query(User).filter(
        User.uid == uid
    ).first()
    target_user = db.query(User).filter(
        User.uid == target_uid
    ).first()
    if user is None or target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="존재하지 않는 사용자입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    follow_follower = db.query(Follow).filter(
        Follow.follower_uid == user.uid,
        Follow.following_uid == target_user.uid
    ).first()
    if follow_follower is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='이미 팔로우한 사용자 입니다.'
        )

    follow_follower = Follow(
        follower_uid=user.uid,
        following_uid=target_user.uid,
    )
    db.add(follow_follower)
    db.commit()

    return target_user

@router.delete("/follow/{target_uid}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_following(
        target_uid: str,
        user_data: Dict[str, Any] = Depends(verify_user_token),
        db: Session = Depends(get_db)
):
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="로그인한 유저만 사용 가능합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    uid = user_data["sub"]
    user = db.query(User).filter(
        User.uid == uid
    ).first()
    target_user = db.query(User).filter(
        User.uid == target_uid
    ).first()
    if user is None or target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="존재하지 않는 사용자입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    follow_follower = db.query(Follow).filter(
        Follow.follower_uid == user.uid,
        Follow.following_uid == target_user.uid
    ).first()

    if follow_follower is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='해당 유저를 팔로우 하지 않습니다.'
        )

    db.delete(follow_follower)
    db.commit()

    return target_user

@router.get("/follow/follower", response_model=List[FollowingSchema], status_code=status.HTTP_200_OK)
async def cancel_following(
        size: int = 20,
        page: int = 1,
        user_data: Dict[str, Any] = Depends(verify_user_token),
        db: Session = Depends(get_db)
):
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="로그인한 유저만 사용 가능합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    uid = user_data["sub"]
    user = db.query(User).filter(
        User.uid == uid
    ).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="존재하지 않는 사용자입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    following_list = db.query(Follow).filter(
        Follow.follower_uid == user.uid,
    ).offset((page - 1) * size).limit(size).all()

    user_list = []
    for following in following_list:
        following_info = following.following
        user_list.append({
            'uid': following_info.uid,
            'name': following_info.name,
            'email': following_info.email,
            'drone': following_info.drone,
            'image': following_info.image,
            'one_liner': following_info.one_liner,
        })

    return user_list
