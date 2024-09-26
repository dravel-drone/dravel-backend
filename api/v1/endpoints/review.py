import uuid
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.staticfiles import StaticFiles

from core.auth import verify_user_token
from database.mariadb_session import get_db
from models import (
    Review as ReviewModel,
    Dronespot as DronespotModel,
    User as UserModel,
    UserReviewLike as UserReviewLikeModel,
    ReviewReport as ReviewReportModel,
)
from core.config import settings
import os

from schemas import Review, ReviewDronespot

router = APIRouter()


@router.post("/review/{drone_spot_id}", response_model=ReviewDronespot, status_code=200)
async def create_review(
        drone_spot_id: int,
        comment: str = Form(...),
        drone_type: str = Form(...),
        date: str = Form(...),
        drone: str = Form(...),
        permit_flight: int = Form(...),
        permit_camera: int = Form(...),
        file: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        user: Dict[str, Any] = Depends(verify_user_token)
):
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
        permit_flight=permit_flight,
        permit_camera=permit_camera,
        drone=drone,
        flight_date=date,
        comment=comment
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)

    photo_url = None
    if file:
        file_extension = os.path.splitext(file.filename)[1]
        new_filename = f"review_{str(uuid.uuid4())}{file_extension}"
        save_path = os.path.join(settings.MEDIA_DIR, new_filename)
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
        "drone": db_review.drone,
        "date": str(db_review.flight_date),
        "comment": db_review.comment,
        "photo": db_review.photo_url,
        "like_count": 0,
        "is_like": is_like
    }

    return JSONResponse(content=response_data, status_code=200)

@router.patch("/review/{review_id}", response_model=Review, status_code=200)
async def patch_review(
        review_id: int,
        comment: Optional[str] = Form(None),
        drone_type: Optional[str] = Form(None),
        date: Optional[str] = Form(None),
        drone: Optional[str] = Form(None),
        file: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        user: Dict[str, Any] = Depends(verify_user_token)
):
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
        "drone": drone,
        "flight_date": date,
        "comment": comment
    }

    for key, value in new_data.items():
        if value is not None:
            setattr(db_review, key, value)

    if file:
        file_extension = os.path.splitext(file.filename)[1]
        new_filename = f"review_{str(uuid.uuid4())}{file_extension}"
        save_path = os.path.join(settings.MEDIA_DIR, new_filename)
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


@router.post("/like/review/{review_id}", status_code=200)
async def like_review(
        review_id: int,
        db: Session = Depends(get_db),
        user: Dict[str, Any] = Depends(verify_user_token)
):
    user_db = db.query(UserModel).filter(UserModel.uid == user.get("sub")).first()
    if not user_db:
        raise HTTPException(
            status_code=404,
            detail="해당 유저를 찾을 수 없습니다."
        )

    like_exists = db.query(UserReviewLikeModel).filter(
        UserReviewLikeModel.user_uid == user_db.uid,
        UserReviewLikeModel.review_id == review_id
    ).first()
    if like_exists:
        raise HTTPException(
            status_code=400,
            detail="이미 해당 리뷰에 좋아요를 눌렀습니다."
        )

    new_like = UserReviewLikeModel(
        user_uid=user_db.uid,
        review_id=review_id
    )
    db.add(new_like)
    db.commit()

    return JSONResponse(content={"메시지": "해당 리뷰에 좋아요 반영이 되었습니다."}, status_code=200)


@router.delete("/like/review/{review_id}", status_code=200)
async def unlike_review(
        review_id: int,
        db: Session = Depends(get_db),
        user: Dict[str, Any] = Depends(verify_user_token)
):
    user_db = db.query(UserModel).filter(UserModel.uid == user.get("sub")).first()
    if not user_db:
        raise HTTPException(
            status_code=404,
            detail="해당 유저를 찾을 수 없습니다."
        )

    like_exists = db.query(UserReviewLikeModel).filter(
        UserReviewLikeModel.user_uid == user_db.uid,
        UserReviewLikeModel.review_id == review_id
    ).first()

    if not like_exists:
        raise HTTPException(
            status_code=400,
            detail="좋아요를 누른 리뷰가 아닙니다."
        )

    db.delete(like_exists)
    db.commit()

    return JSONResponse(content={"메시지": "해당 리뷰에 좋아요를 취소했습니다."}, status_code=200)

@router.get("/review/like/{user_id}", response_model=list[ReviewDronespot], status_code=200)
def get_like_user_reviews(
    user_id: str,
    page_num: int = Query(1, alias="page_num"),
    size: int = Query(10, alias="size"),
    db: Session = Depends(get_db),
    user: Optional[Dict[str, Any]] = Depends(verify_user_token)
):
    if not user or user.get("sub") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden"
        )

    liked_review = (
        db.query(ReviewModel)
        .join(UserReviewLikeModel, ReviewModel.id == UserReviewLikeModel.review_id)
        .filter(UserReviewLikeModel.user_uid == user_id)
        .order_by(UserReviewLikeModel.created_at.desc())
        .offset((page_num - 1) * size).limit(size).all()
    )

    if not liked_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No liked review found"
        )

    response = []
    for review in liked_review:
        # 로그인한 유저일 경우, 좋아요 여부 확인
        if user:
            is_like = db.query(UserReviewLikeModel).filter(
                UserReviewLikeModel.review_id == review.id,
                UserReviewLikeModel.user_uid == user['sub']
            ).count()
        else:
            is_like = 0  # 로그인하지 않은 경우

        like_count = db.query(UserReviewLikeModel).filter(UserReviewLikeModel.review_id == review.id).count()
        response.append(ReviewDronespot(
            id=review.id,
            writer=None if review.writer_uid is None else {
                "uid": review.writer_uid,
                "name": review.user.name
            },
            place_name=review.dronespot.name,
            permit={
                "flight": review.permit_flight,
                "camera": review.permit_camera
            },
            drone_type=review.drone_type,
            drone=review.drone,
            date=review.flight_date.isoformat(),
            comment=review.comment if review.comment else "",
            photo=review.photo_url if review.photo_url else "",
            like_count=like_count,
            is_like=is_like
        ))

    return response

@router.get("/userReview/{user_id}", response_model=list[ReviewDronespot], status_code=200)
def get_user_reviews(
    user_id: str,
    page_num: int = Query(1, alias="page_num"),
    size: int = Query(10, alias="size"),
    order: int = Query(0, alias="order"),  # 0: 최신순, 1: 좋아요순
    db: Session = Depends(get_db),
    user: Optional[Dict[str, Any]] = Depends(verify_user_token)
):

    db_review = db.query(ReviewModel).filter(ReviewModel.writer_uid == user_id)

    if order == 1:
        # 좋아요 순 정렬
        db_review = db_review.outerjoin(UserReviewLikeModel).group_by(ReviewModel.id).order_by(func.count(UserReviewLikeModel.review_id).desc())
    else:
        # 최신순 정렬
        db_review = db_review.order_by(ReviewModel.flight_date.desc())

    # 페이징
    reviews = db_review.offset((page_num - 1) * size).limit(size).all()

    response = []
    for review in reviews:
        # 로그인한 유저일 경우, 좋아요 여부 확인
        if user:
            is_like = db.query(UserReviewLikeModel).filter(
                UserReviewLikeModel.review_id == review.id,
                UserReviewLikeModel.user_uid == user['sub']
            ).count()
        else:
            is_like = 0  # 로그인하지 않은 경우

        like_count = db.query(UserReviewLikeModel).filter(UserReviewLikeModel.review_id == review.id).count()
        response.append(ReviewDronespot(
            id=review.id,
            writer=None if review.writer_uid is None else {
                "uid": review.writer_uid,
                "name": review.user.name
            },
            place_name=review.dronespot.name,
            permit={
                "flight": review.permit_flight,
                "camera": review.permit_camera
            },
            drone_type=review.drone_type,
            date=review.flight_date.isoformat(),
            comment=review.comment if review.comment else "",
            photo=review.photo_url if review.photo_url else "",
            like_count=like_count,
            is_like=is_like,
            drone=review.drone
        ))

    return response


@router.get("/spotReview/{drone_spot_id}", response_model=list[ReviewDronespot], status_code=200)
def get_spot_reviews(
    drone_spot_id: int,
    page_num: int = Query(1, alias="page_num"),
    size: int = Query(10, alias="size"),
    order: int = Query(0, alias="order"),  # 0: 최신순, 1: 좋아요순
    db: Session = Depends(get_db),
    user: Optional[Dict[str, Any]] = Depends(verify_user_token)
):

    db_review = db.query(ReviewModel).filter(ReviewModel.dronespot_id == drone_spot_id)

    if order == 1:
        # 좋아요 순 정렬
        db_review = db_review.outerjoin(UserReviewLikeModel).group_by(ReviewModel.id).order_by(func.count(UserReviewLikeModel.review_id).desc())
    else:
        # 최신순 정렬
        db_review = db_review.order_by(ReviewModel.id.desc())

    # 페이징
    reviews = db_review.offset((page_num - 1) * size).limit(size).all()

    response = []
    for review in reviews:
        # 로그인한 유저일 경우, 좋아요 여부 확인
        if user:
            is_like = db.query(UserReviewLikeModel).filter(
                UserReviewLikeModel.review_id == review.id,
                UserReviewLikeModel.user_uid == user['sub']
            ).count()
        else:
            is_like = 0  # 로그인하지 않은 경우

        like_count = db.query(UserReviewLikeModel).filter(UserReviewLikeModel.review_id == review.id).count()
        response.append(Review(
            id=review.id,
            writer=None if review.writer_uid is None else {
                "uid": review.writer_uid,
                "name": review.user.name
            },
            place_name=review.dronespot.name,
            permit={
                "flight": review.permit_flight,
                "camera": review.permit_camera
            },
            drone_type=review.drone_type,
            date=review.flight_date.isoformat(),
            comment=review.comment if review.comment else "",
            photo=review.photo_url if review.photo_url else "",
            like_count=like_count,
            is_like=is_like,
            drone=review.drone
        ))

    return response


@router.get("/review/{review_id}", response_model=list[Review], status_code=200)
def get_review(
    review_id: int,
    db: Session = Depends(get_db),
    user: Optional[Dict[str, Any]] = Depends(verify_user_token)
):

    db_review = db.query(ReviewModel).filter(ReviewModel.id == review_id).first()
    if not db_review:
        raise HTTPException(status_code=400, detail="존재하지 않는 리뷰 아이디입니다.")

    response = []
    # 로그인한 유저일 경우, 좋아요 여부 확인
    if user:
        is_like = db.query(UserReviewLikeModel).filter(
            UserReviewLikeModel.review_id == db_review.id,
            UserReviewLikeModel.user_uid == user['sub']
        ).count()
    else:
        is_like = 0  # 로그인하지 않은 경우

    like_count = db.query(UserReviewLikeModel).filter(UserReviewLikeModel.review_id == review_id).count()
    response.append(Review(
        id=review_id,
        writer=None if db_review.writer_uid is None else {
            "uid": db_review.writer_uid,
            "name": db_review.user.name
        },
        place_name=db_review.dronespot.name,
        permit={
            "flight": db_review.permit_flight,
            "camera": db_review.permit_camera
        },
        drone_type=db_review.drone_type,
        date=db_review.flight_date.isoformat(),
        comment=db_review.comment if db_review.comment else "",
        photo=db_review.photo_url if db_review.photo_url else "",
        like_count=like_count,
        is_like=is_like
    ))

    return response


@router.get("/trend/review", response_model=List[Review], status_code=200)
def get_trend_reviews(
    page_num: int = 1,
    size: int = 10,
    db: Session = Depends(get_db),
    user: Optional[Dict[str, Any]] = Depends(verify_user_token)
):

    reviews = (db.query(ReviewModel).order_by(func.random())
               .offset((page_num - 1) * size).limit(size).all())

    response = []
    for review in reviews:
        # 로그인한 유저일 경우, 좋아요 여부 확인
        if user:
            is_like = db.query(UserReviewLikeModel).filter(
                UserReviewLikeModel.review_id == review.id,
                UserReviewLikeModel.user_uid == user['sub']
            ).count()
        else:
            is_like = 0  # 로그인하지 않은 경우

        like_count = db.query(UserReviewLikeModel).filter(UserReviewLikeModel.review_id == review.id).count()
        response.append(Review(
            id=review.id,
            writer=None if review.writer_uid is None else {
                "uid": review.writer_uid,
                "name": review.user.name
            },
            place_name=review.dronespot.name,
            permit={
                "flight": review.permit_flight,
                "camera": review.permit_camera
            },
            drone_type=review.drone_type,
            date=review.flight_date.isoformat(),
            comment=review.comment if review.comment else "",
            photo=review.photo_url if review.photo_url else "",
            like_count=like_count,
            is_like=is_like
        ))

    return response

@router.delete("/review/{review_id}", status_code=200)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    user: Optional[Dict[str, Any]] = Depends(verify_user_token)
):
    user_db = db.query(UserModel).filter(UserModel.uid == user.get("sub")).first()
    if not user_db:
        raise HTTPException(
            status_code=404,
            detail="해당 유저를 찾을 수 없습니다."
        )
    db_review = db.query(ReviewModel).filter(ReviewModel.id == review_id).first()
    if not db_review:
        raise HTTPException(status_code=400, detail="존재하지 않는 리뷰 아이디입니다.")

    if user_db.is_admin == 1:
        db.delete(db_review)
        db.commit()
    elif user_db.is_admin == 0 and user_db.uid == db_review.writer_uid:
        db.delete(db_review)
        db.commit()
    else:
        raise HTTPException(
            status_code=400,
            detail="접근할 수 없는 리뷰입니다."
        )

    return {"message": "해당 리뷰가 삭제되었습니다."}

@router.post('/review/report/{review_id}', status_code=status.HTTP_204_NO_CONTENT)
async def report_review(
        review_id: int,
        db: Session = Depends(get_db),
        user_data: Optional[Dict[str, Any]] = Depends(verify_user_token)
):
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="로그인한 유저만 사용 가능합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    uid = user_data["sub"]
    user = db.query(UserModel).filter(
        UserModel.uid == uid
    ).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="존재하지 않는 사용자입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    review = db.query(ReviewModel).filter(
        ReviewModel.id == review_id
    ).first()
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="존재하지 않는 리뷰입니다.",
        )

    review_report = db.query(ReviewReportModel).filter(
        ReviewReportModel.review_id == review_id,
        ReviewReportModel.user_uid == uid
    ).first()
    if review_report is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 신고한 리뷰입니다.",
        )

    review_report = ReviewReportModel(
        review_id=review_id,
        user_uid=uid
    )
    db.add(review_report)
    db.commit()

    report_count = db.query(func.count(ReviewReportModel.id)).filter(
        ReviewReportModel.review_id == review_id,
        ReviewReportModel.user_uid == uid
    ).scalar()
    print(report_count)
    if report_count >= 10:
        review.is_reported = 1
        db.commit()
