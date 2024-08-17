from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.staticfiles import StaticFiles

from core.auth import verify_user_token
from database.mariadb_session import get_db
from models import Review as ReviewModel, Dronespot as DronespotModel, User as UserModel, UserReviewLike as UserReviewLikeModel
import os

from schemas import Review

router = APIRouter()
MEDIA_DIR = "media"
router.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")


@router.post("/review/{drone_spot_id}", response_model=Review, status_code=200)
async def create_review(
        drone_spot_id: int,
        comment: str = Form(...),
        drone_type: str = Form(...),
        date: str = Form(...),
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        #user: Dict[str, Any] = Depends(verify_user_token)
):
    user = {"sub": "0314a071-bc26-4243-8c52-f183de15d0f4"}
    user_db = db.query(UserModel).filter(UserModel.uid == user.get("sub")).first()
    print(user_db)
    # 드론 스팟 확인
    drone_spot = db.query(DronespotModel).filter(DronespotModel.id == drone_spot_id).first()
    if not drone_spot:
        raise HTTPException(status_code=404, detail="드론 스팟을 찾을 수 없습니다.")

    # 리뷰 데이터 생성
    db_review = ReviewModel(
        writer_uid=user_db.uid,
        dronespot_id=drone_spot_id,
        drone_type=drone_type,
        permit_flight=drone_spot.permit_flight,
        permit_camera=drone_spot.permit_camera,
        drone="???",
        flight_date=date,
        comment=comment
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)

    photo_url = None
    if file:
        file_extension = os.path.splitext(file.filename)[1]
        new_filename = f"review_{drone_spot_id}_{date}{file_extension}"
        save_path = os.path.join(MEDIA_DIR, new_filename)
        with open(save_path, "wb") as f:
            f.write(await file.read())
        photo_url = f"/media/{new_filename}"
        print(photo_url)
        db_review.photo_url = photo_url
        db.commit()
        db.refresh(db_review)

    like_count = 0,  # 초기 좋아요 개수
    is_like = 0  # 초기 좋아요 상태
    response_data = {
        "id": db_review.id,
        "writer": {
            "uid": user_db.uid,
            "name": user_db.name
        },
        "place_name": drone_spot.name,
        "permit": {
            "flight": db_review.permit_flight,
            "camera": db_review.permit_camera
        },
        "drone_type": db_review.drone_type,
        "date": str(db_review.flight_date),
        "comment": db_review.comment,
        "photo": db_review.photo_url,
        "like_count": like_count,
        "is_like": is_like
    }

    return JSONResponse(content=response_data, status_code=200)

@router.patch("/review/{review_id}", response_model=Review, status_code=200)
async def create_review(
        review_id: int,
        comment: str = Form(...),
        drone_type: str = Form(...),
        date: str = Form(...),
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        #user: Dict[str, Any] = Depends(verify_user_token)
):
    user = {"sub": "0314a071-bc26-4243-8c52-f183de15d0f4"}
    user_db = db.query(UserModel).filter(UserModel.uid == user.get("sub")).first()

    db_review = db.query(ReviewModel).filter(ReviewModel.id == review_id).first()
    if not db_review:
        raise HTTPException(status_code=404, detail="해당 리뷰를 찾을 수 없습니다.")

    # 드론 스팟 확인
    drone_spot = db.query(DronespotModel).filter(DronespotModel.id == db_review.dronespot_id).first()
    if not drone_spot:
        raise HTTPException(status_code=404, detail="드론 스팟을 찾을 수 없습니다.")

    # 리뷰 데이터 생성
    new_data = {
        "writer_uid": user_db.uid,
        "drone_type": drone_type,
        "permit_flight": db_review.permit_flight,
        "permit_camera": db_review.permit_camera,
        "drone": "???",
        "flight_date": date,
        "comment": comment
    }

    for key, value in new_data.items():
        if value is not None:
            setattr(db_review, key, value)

    if file:
        file_extension = os.path.splitext(file.filename)[1]
        new_filename = f"review_{db_review.dronespot_id}_{date}{file_extension}"
        save_path = os.path.join(MEDIA_DIR, new_filename)
        with open(save_path, "wb") as f:
            f.write(await file.read())
        photo_url = f"/media/{new_filename}"
        db_review.photo_url = photo_url

    db.commit()
    db.refresh(db_review)

    is_like = (
        db.query(UserReviewLikeModel)
        .filter(
            UserReviewLikeModel.user_uid == user_db.uid,
            UserReviewLikeModel.review_id == review_id
        )
        .count()
    )

    likes_count = db.query(func.count(UserReviewLikeModel.user_uid)).filter(
        UserReviewLikeModel.review_id == review_id).scalar()

    response_data = {
        "id": db_review.id,
        "writer": {
            "uid": user_db.uid,
            "name": user_db.name
        },
        "place_name": drone_spot.name,
        "permit": {
            "flight": db_review.permit_flight,
            "camera": db_review.permit_camera
        },
        "drone_type": db_review.drone_type,
        "date": str(db_review.flight_date),
        "comment": db_review.comment,
        "photo": db_review.photo_url,
        "like_count": likes_count,
        "is_like": is_like
    }

    return JSONResponse(content=response_data, status_code=200)