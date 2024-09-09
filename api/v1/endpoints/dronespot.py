import asyncio
import os
import uuid
from math import radians
import random
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.staticfiles import StaticFiles

from core.getplace import save_place
from models import UserDronespotLike as UserDronespotLikeModel, Dronespot as DronespotModel, User as UserModel, TrendDronespot, \
    Review as ReviewModel, Course as CourseModel, Place as PlaceModel, UserReviewLike, DronePlace as DronePlaceModel, \
    CourseVisit as CourseVisitModel
from schemas import Dronespot, Permit, Area, Location, DronespotResponse
from core.auth import verify_user_token
from database.mariadb_session import get_db
from starlette.responses import JSONResponse

from core.config import settings

router = APIRouter()

@router.post("/dronespot", response_model=Dronespot, status_code=201)
async def create_dronespot(
        name: str = Form(...),
        lat: float = Form(...),
        lon: float = Form(...),
        address: str = Form(...),
        comment: str = Form(...),
        permit_flight: int = Form(...),
        permit_camera: int = Form(...),
        drone_type: int = Form(...),
        file: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        user_data: Dict[str, Any] = Depends(verify_user_token)
):
    if not user_data.get("level"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db_dronespot = DronespotModel(
        name=name,
        lat=lat,
        lon=lon,
        address=address,
        comment=comment,
        permit_flight=permit_flight,
        permit_camera=permit_camera,
        drone_type=drone_type
    )

    db.add(db_dronespot)
    db.commit()
    db.refresh(db_dronespot)

    photo_url = None
    if file:
        file_extension = os.path.splitext(file.filename)[1]
        new_filename = f"dronespot_{str(uuid.uuid4())}{file_extension}"
        save_path = os.path.join(settings.MEDIA_DIR, new_filename)
        with open(save_path, "wb") as f:
            f.write(await file.read())
        photo_url = f"/media/{new_filename}"

        db_dronespot.photo_url = photo_url
        db.commit()
        db.refresh(db_dronespot)

    likes_count = 0
    reviews_count = 0
    is_like = 0
    area_data = [
        {"id": 1, "name": "Area 1"},
        {"id": 2, "name": "Area 2"}
    ]

    # 주변장소 디비에 저장
    dronespotID = db_dronespot.id
    await save_place(dronespotID)

    return {
        "id": db_dronespot.id,
        "name": db_dronespot.name,
        "is_like": is_like,
        "location": {
            "lat": db_dronespot.lat,
            "lon": db_dronespot.lon,
            "address": db_dronespot.address
        },
        "likes_count": likes_count,
        "reviews_count": reviews_count,
        "photo": db_dronespot.photo_url,
        "comment": db_dronespot.comment,
        "area": area_data,
        "permit": {
            "flight": db_dronespot.permit_flight,
            "camera": db_dronespot.permit_camera
        },
        "drone_type": drone_type
    }

@router.patch("/dronespot/{dronespot_id}", response_model=Dronespot)
async def update_dronespot(
        dronespot_id: int,
        name: Optional[str] = Form(None),
        lat: Optional[float] = Form(None),
        lon: Optional[float] = Form(None),
        address: Optional[str] = Form(None),
        comment: Optional[str] = Form(None),
        permit_flight: Optional[int] = Form(None),
        permit_camera: Optional[int] = Form(None),
        drone_type: int = Form(...),
        file: Optional[UploadFile] = File(None),
        db: Session = Depends(get_db),
        user_data: Dict[str, Any] = Depends(verify_user_token)
):
    if not user_data.get("level"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db_dronespot = db.query(DronespotModel).filter(DronespotModel.id == dronespot_id).first()
    if not db_dronespot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dronespot not found"
        )

    update_data = {
        "name": name,
        "lat": lat,
        "lon": lon,
        "address": address,
        "comment": comment,
        "permit_flight": permit_flight,
        "permit_camera": permit_camera,
        "drone_type": drone_type
    }

    for key, value in update_data.items():
        if value is not None:
            setattr(db_dronespot, key, value)

    if file:
        file_extension = os.path.splitext(file.filename)[1]
        new_filename = f"dronespot_{str(uuid.uuid4())}{file_extension}"
        save_path = os.path.join(settings.MEDIA_DIR, new_filename)
        with open(save_path, "wb") as f:
            f.write(await file.read())
        db_dronespot.photo_url = f"/media/{new_filename}"

    db.commit()
    db.refresh(db_dronespot)

    is_like = (
        db.query(UserDronespotLikeModel)
        .filter(
            UserDronespotLikeModel.user_uid == user_data["sub"],
            UserDronespotLikeModel.drone_spot_id == dronespot_id
        )
        .count()
    )

    likes_count = db.query(func.count(UserDronespotLikeModel.user_uid)).filter(
        UserDronespotLikeModel.drone_spot_id == dronespot_id).scalar()
    reviews_count = db.query(func.count(ReviewModel.id)).filter(
                ReviewModel.dronespot_id == dronespot_id).scalar()

    return Dronespot(
        id=db_dronespot.id,
        name=db_dronespot.name,
        is_like=is_like,
        location=Location(
            lat=db_dronespot.lat,
            lon=db_dronespot.lon,
            address=db_dronespot.address
        ),
        likes_count=likes_count,
        reviews_count=reviews_count,
        photo=db_dronespot.photo_url,
        comment=db_dronespot.comment,
        area=[Area(id=1, name="Area 1"), Area(id=2, name="Area 2")],
        permit=Permit(
            flight=db_dronespot.permit_flight,
            camera=db_dronespot.permit_camera
        ),
        drone_type=drone_type
    )


@router.delete("/dronespot/{drone_spot_id}", status_code=204)
async def delete_dronespot(
        drone_spot_id: int,
        db: Session = Depends(get_db),
        user_data: Dict[str, Any] = Depends(verify_user_token)
):
    if not user_data.get("level"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db_dronespot = db.query(DronespotModel).filter(DronespotModel.id == drone_spot_id).first()
    if not db_dronespot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dronespot not found"
        )

    db.delete(db_dronespot)
    db.commit()

    return JSONResponse(content={"message": "Delete successfully"})

@router.post("/like/dronespot/{dronespot_id}", status_code=204)
async def like_dronespot(
        dronespot_id: int,
        db: Session = Depends(get_db),
        user_data: Dict[str, Any] = Depends(verify_user_token)
):
    user_uid = user_data.get("sub")

    user = db.query(UserModel).filter(UserModel.uid == user_uid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    dronespot = db.query(DronespotModel).filter(DronespotModel.id == dronespot_id).first()
    if not dronespot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dronespot not found"
        )

    like_exists = db.query(UserDronespotLikeModel).filter(
        UserDronespotLikeModel.user_uid == user_uid,
        UserDronespotLikeModel.drone_spot_id == dronespot_id
    ).first()
    if like_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already liked this dronespot"
        )

    new_like = UserDronespotLikeModel(
        user_uid=user_uid,
        drone_spot_id=dronespot_id
    )
    db.add(new_like)
    db.commit()

    return JSONResponse(content={"message": "Liked successfully"})

@router.delete("/like/dronespot/{dronespot_id}", status_code=204)
async def unlike_dronespot(
        dronespot_id: int,
        db: Session = Depends(get_db),
        user_data: Dict[str, Any] = Depends(verify_user_token)
):
    user_uid = user_data.get("sub")
    print(user_uid)

    user = db.query(UserModel).filter(UserModel.uid == user_uid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    dronespot = db.query(DronespotModel).filter(DronespotModel.id == dronespot_id).first()
    if not dronespot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dronespot not found"
        )

    like_exists = db.query(UserDronespotLikeModel).filter(
        UserDronespotLikeModel.user_uid == user_uid,
        UserDronespotLikeModel.drone_spot_id == dronespot_id
    ).first()
    if not like_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has not liked this dronespot"
        )

    db.delete(like_exists)
    db.commit()

    return JSONResponse(content={"message": "UnLiked successfully"})

@router.get("/dronespot/like/{user_uid}", response_model=List[Dronespot])
async def get_liked_dronespots(
        user_uid: str,
        db: Session = Depends(get_db),
        user_data: Optional[Dict[str, Any]] = Depends(verify_user_token)
):

    if not user_data or user_data.get("sub") != user_uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden"
        )

    liked_dronespots = (
        db.query(DronespotModel)
        .join(UserDronespotLikeModel, DronespotModel.id == UserDronespotLikeModel.drone_spot_id)
        .filter(UserDronespotLikeModel.user_uid == user_uid)
        .all()
    )

    if not liked_dronespots:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No liked dronespots found"
        )

    response_data = []
    for dronespot in liked_dronespots:
        dronespot_data = {
            "id": dronespot.id,
            "name": dronespot.name,
            "is_like": 1,
            "location": {
                "lat": dronespot.lat,
                "lon": dronespot.lon,
                "address": dronespot.address
            },
            "likes_count": db.query(func.count(UserDronespotLikeModel.user_uid)).filter(
                UserDronespotLikeModel.drone_spot_id == dronespot.id
            ).scalar(),
            "reviews_count": db.query(func.count(ReviewModel.id)).filter(
                ReviewModel.dronespot_id == dronespot.id
            ).scalar(),
            "photo": dronespot.photo_url,
            "comment": dronespot.comment,
            "area": [
                {"id": 1, "name": "Area 1"},
                {"id": 2, "name": "Area 2"}
            ],
            "permit": {
                "flight": dronespot.permit_flight,
                "camera": dronespot.permit_camera
            }
        }
        response_data.append(dronespot_data)

    return response_data

@router.get("/dronespot/popular", response_model=List[Dronespot])
async def get_popular_dronespots(
        page_num: int = Query(1, ge=1),
        size: int = Query(10, ge=1),
        db: Session = Depends(get_db),
        user_data: Optional[Dict[str, Any]] = Depends(verify_user_token)
):
    dronespots_query = db.query(
        DronespotModel,
        func.count(UserDronespotLikeModel.user_uid).label('likes_count')
    ).outerjoin(UserDronespotLikeModel, DronespotModel.id == UserDronespotLikeModel.drone_spot_id) \
     .group_by(DronespotModel.id) \
     .order_by(func.count(UserDronespotLikeModel.user_uid).desc()) \
     .offset((page_num - 1) * size) \
     .limit(size)

    dronespots = dronespots_query.all()

    if not dronespots:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No popular dronespots found"
        )

    user_uid = user_data.get("sub") if user_data else None

    response_data = [
        {
            "id": dronespot.id,
            "name": dronespot.name,
            "is_like": 1 if user_uid and db.query(UserDronespotLikeModel).filter(
                UserDronespotLikeModel.user_uid == user_uid,
                UserDronespotLikeModel.drone_spot_id == dronespot.id
            ).first() else 0,
            "location": {
                "lat": dronespot.lat,
                "lon": dronespot.lon,
                "address": dronespot.address
            },
            "likes_count": likes_count,
            "reviews_count": db.query(func.count(ReviewModel.id)).filter(
                ReviewModel.dronespot_id == dronespot.id
            ).scalar(),
            "photo": dronespot.photo_url,
            "comment": dronespot.comment,
            "area": [
                {"id": 1, "name": "Area 1"},
                {"id": 2, "name": "Area 2"}
            ],
            "permit": {
                "flight": dronespot.permit_flight,
                "camera": dronespot.permit_camera
            }
        }
        for dronespot, likes_count in dronespots
    ]

    return response_data

@router.get("/dronespot/keyword/popular", response_model=List[Dronespot])
async def get_popular_dronespots_by_keyword(
    page_num: int = Query(1, ge=1),
    size: int = Query(10, ge=1),
    db: Session = Depends(get_db),
    user_data: Optional[Dict[str, Any]] = Depends(verify_user_token)
):
    dronespots_query = (
        db.query(DronespotModel)
        .join(TrendDronespot, DronespotModel.id == TrendDronespot.dronespot_id)
        .order_by(TrendDronespot.count.desc()).offset((page_num - 1) * size).limit(size)
    )

    dronespots = dronespots_query.all()

    if not dronespots:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No popular dronespots found"
        )

    user_uid = user_data.get("sub") if user_data else None

    response_data = [
        {
            "id": dronespot.id,
            "name": dronespot.name,
            "is_like": 1 if user_uid and db.query(UserDronespotLikeModel).filter(
                UserDronespotLikeModel.user_uid == user_uid,
                UserDronespotLikeModel.drone_spot_id == dronespot.id
            ).first() else 0,
            "location": {
                "lat": dronespot.lat,
                "lon": dronespot.lon,
                "address": dronespot.address
            },
            "likes_count": db.query(func.count(UserDronespotLikeModel.user_uid)).filter(
                UserDronespotLikeModel.drone_spot_id == dronespot.id
            ).scalar(),
            "reviews_count": db.query(func.count(ReviewModel.id)).filter(
                ReviewModel.dronespot_id == dronespot.id
            ).scalar(),
            "photo": dronespot.photo_url,
            "comment": dronespot.comment,
            "area": [
                {"id": 1, "name": "Area 1"},
                {"id": 2, "name": "Area 2"}
            ],
            "permit": {
                "flight": dronespot.permit_flight,
                "camera": dronespot.permit_camera
            }
        }
        for dronespot in dronespots
    ]

    return response_data

@router.get("/dronespot/search", response_model=List[Dronespot])
async def search_dronespots(
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
    area: Optional[float] = Query(None),
    keyword: Optional[str] = Query(None),
    drone_type: Optional[int] = Query(None),
    page_num: int = Query(1, ge=1),
    size: int = Query(10, ge=1),
    db: Session = Depends(get_db),
    user_data: Optional[Dict[str, Any]] = Depends(verify_user_token)
):

    if (lat is not None or lon is not None or area is not None) and (lat is None or lon is None or area is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="lat, lon, and area must all be provided if any are provided"
        )

    dronespots_query = db.query(DronespotModel)

    if lat is not None and lon is not None and area is not None:
        lat_radians = radians(lat)
        lon_radians = radians(lon)

        distance_formula = (
            6371 * func.acos(
                func.cos(lat_radians) * func.cos(func.radians(DronespotModel.lat)) *
                func.cos(func.radians(DronespotModel.lon) - lon_radians) +
                func.sin(lat_radians) * func.sin(func.radians(DronespotModel.lat))
            )
        )

        dronespots_query = dronespots_query.filter(distance_formula <= area)

    if keyword:
        starting_with_keyword = dronespots_query.filter(
            DronespotModel.name.ilike(f"{keyword}%")
        )
        containing_keyword = dronespots_query.filter(
            DronespotModel.name.ilike(f"%{keyword}%")
        ).filter(
            ~DronespotModel.id.in_([spot.id for spot in starting_with_keyword])
        )
        dronespots_query = starting_with_keyword.union_all(containing_keyword)

        for dronespot in starting_with_keyword.all() + containing_keyword.all():
            trend_spot = db.query(TrendDronespot).filter(TrendDronespot.dronespot_id == dronespot.id).first()
            if trend_spot:
                trend_spot.count += 1
            else:
                trend_spot = TrendDronespot(dronespot_id=dronespot.id, count=1)
                db.add(trend_spot)
            db.add(dronespot)

        db.commit()

    if drone_type:
        dronespots_query = dronespots_query.filter(DronespotModel.drone_type == drone_type)

    if not lat and not lon and not area and not keyword and not drone_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of lat/lon/area, keyword, or drone_type must be provided."
        )

    dronespots_query = dronespots_query.order_by(DronespotModel.name).offset((page_num - 1) * size).limit(size)

    dronespots = dronespots_query.all()

    if not dronespots:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No dronespots found"
        )

    user_uid = user_data.get("sub") if user_data else None

    response_data = [
        {
            "id": dronespot.id,
            "name": dronespot.name,
            "is_like": 1 if user_uid and db.query(UserDronespotLikeModel).filter(
                UserDronespotLikeModel.user_uid == user_uid,
                UserDronespotLikeModel.drone_spot_id == dronespot.id
            ).first() else 0,
            "location": {
                "lat": dronespot.lat,
                "lon": dronespot.lon,
                "address": dronespot.address
            },
            "likes_count": db.query(func.count(UserDronespotLikeModel.user_uid)).filter(
                UserDronespotLikeModel.drone_spot_id == dronespot.id
            ).scalar(),
            "reviews_count": db.query(func.count(ReviewModel.id)).filter(
                ReviewModel.dronespot_id == dronespot.id
            ).scalar(),
            "photo": dronespot.photo_url,
            "comment": dronespot.comment,
            "drone_type": dronespot.drone_type,
            "area": [
                {"id": 1, "name": "Area 1"},
                {"id": 2, "name": "Area 2"}
            ],
            "permit": {
                "flight": dronespot.permit_flight,
                "camera": dronespot.permit_camera
            }
        }
        for dronespot in dronespots
    ]

    return response_data

@router.get("/dronespot/all", response_model=List[Dronespot])
async def get_all_dronespot(
    drone_type: Optional[int] = None,
    db: Session = Depends(get_db),
    user_data: Optional[Dict[str, Any]] = Depends(verify_user_token)
):
    dronespots = db.query(DronespotModel)

    if drone_type is not None:
        dronespots = dronespots.filter(DronespotModel.drone_type == drone_type).all()
    else:
        dronespots = dronespots.all()

    if not dronespots:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No dronespots found"
        )

    user_uid = user_data.get("sub") if user_data else None

    response_data = [
        {
            "id": dronespot.id,
            "name": dronespot.name,
            "is_like": 1 if user_uid and db.query(UserDronespotLikeModel).filter(
                UserDronespotLikeModel.user_uid == user_uid,
                UserDronespotLikeModel.drone_spot_id == dronespot.id
            ).first() else 0,
            "location": {
                "lat": dronespot.lat,
                "lon": dronespot.lon,
                "address": dronespot.address
            },
            "likes_count": db.query(func.count(UserDronespotLikeModel.user_uid)).filter(
                UserDronespotLikeModel.drone_spot_id == dronespot.id
            ).scalar(),
            "reviews_count": db.query(func.count(ReviewModel.id)).filter(
                ReviewModel.dronespot_id == dronespot.id
            ).scalar(),
            "photo": dronespot.photo_url,
            "comment": dronespot.comment,
            "drone_type": dronespot.drone_type,
            "area": [
                {"id": 1, "name": "Area 1"},
                {"id": 2, "name": "Area 2"}
            ],
            "permit": {
                "flight": dronespot.permit_flight,
                "camera": dronespot.permit_camera
            }
        }
        for dronespot in dronespots
    ]

    return response_data


@router.get("/dronespot/recommend", response_model=List[Dronespot])
async def recommend_dronespots(
    page_num: int = Query(1, ge=1),
    size: int = Query(10, ge=1),
    db: Session = Depends(get_db),
    user_data: Optional[Dict[str, Any]] = Depends(verify_user_token)
):
    dronespots = db.query(DronespotModel).all()

    if not dronespots:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No dronespots found"
        )
    random.shuffle(dronespots)

    start_index = (page_num - 1) * size
    end_index = start_index + size
    recommend_dronespots = dronespots[start_index:end_index]

    user_uid = user_data.get("sub") if user_data else None

    response_data = [
        {
            "id": dronespot.id,
            "name": dronespot.name,
            "is_like": 1 if user_uid and db.query(UserDronespotLikeModel).filter(
                UserDronespotLikeModel.user_uid == user_uid,
                UserDronespotLikeModel.drone_spot_id == dronespot.id
            ).first() else 0,
            "location": {
                "lat": dronespot.lat,
                "lon": dronespot.lon,
                "address": dronespot.address
            },
            "likes_count": db.query(func.count(UserDronespotLikeModel.user_uid)).filter(
                UserDronespotLikeModel.drone_spot_id == dronespot.id).scalar(),
            "reviews_count": db.query(func.count(ReviewModel.id)).filter(
                ReviewModel.dronespot_id == dronespot.id).scalar(),
            "photo": dronespot.photo_url,
            "comment": dronespot.comment,
            "area": [
                {"id": 1, "name": "Area 1"},
                {"id": 2, "name": "Area 2"}
            ],
            "permit": {
                "flight": dronespot.permit_flight,
                "camera": dronespot.permit_camera
            }
        }
        for dronespot in recommend_dronespots
    ]

    return response_data

@router.get("/dronespot/{dronespot_id}", response_model=DronespotResponse)
async def get_dronespot(
        dronespot_id: int,
        db: Session = Depends(get_db),
        user_data: Optional[Dict[str, Any]] = Depends(verify_user_token)
):

    dronespot = db.query(DronespotModel).filter(DronespotModel.id == dronespot_id).first()
    if not dronespot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dronespot not found"
        )

    likes_count = db.query(func.count(UserDronespotLikeModel.user_uid)).filter(
        UserDronespotLikeModel.drone_spot_id == dronespot_id).scalar()

    is_like = (
        db.query(UserDronespotLikeModel)
        .filter(
            UserDronespotLikeModel.user_uid == user_data["sub"],
            UserDronespotLikeModel.drone_spot_id == dronespot_id
        )
        .count() if user_data and user_data.get("sub") else 0
    )

    reviews = db.query(ReviewModel).filter(ReviewModel.dronespot_id == dronespot_id).order_by(
        ReviewModel.flight_date.desc()).all()

    review_data = []
    for review in reviews:
        writer = db.query(UserModel).filter(UserModel.uid == review.writer_uid).first()
        review_data.append({
            "id": review.id,
            "writer": {"uid": writer.uid, "name": writer.name},
            "place_name": review.dronespot.name,
            "permit": {"flight": review.permit_flight, "camera": review.permit_camera},
            "drone_type": review.drone_type,
            "drone": review.drone,
            "date": review.flight_date.isoformat(),
            "comment": review.comment,
            "photo": review.photo_url,
            "like_count": db.query(func.count(UserReviewLike.user_uid)).filter(
                UserReviewLike.review_id == review.id).scalar(),
            "is_like": 1 if user_data and db.query(UserReviewLike).filter(
                UserReviewLike.user_uid == user_data["sub"],
                UserReviewLike.review_id == review.id
            ).first() else 0
        })

    course_visits = db.query(CourseVisitModel).filter(
        CourseVisitModel.dronespot_id == dronespot_id
    ).group_by(
        CourseVisitModel.course_id,
        CourseVisitModel.dronespot_id
    ).limit(3).all()

    courses = []
    for visit in course_visits:
        course = db.query(CourseModel).filter(CourseModel.id == visit.course_id).first()
        if course:
            # place_info = []
            #
            # if visit.place_id:
            #     place = db.query(PlaceModel).filter(PlaceModel.id == visit.place_id).first()
            #     if place:
            #         place_info.append({
            #             "id": place.id,
            #             "name": place.name,
            #             "photo": place.photo_url
            #         })
            #
            # if visit.dronespot_id:
            #     dronespot_place = db.query(DronespotModel).filter(DronespotModel.id == visit.dronespot_id).first()
            #     if dronespot_place:
            #         place_info.append({
            #             "id": dronespot_place.id,
            #             "name": dronespot_place.name,
            #             "photo": dronespot_place.photo_url
            #         })

            courses.append({
                "id": course.id,
                "name": course.name,
                "content": course.content,
                # "places": place_info,
                "photo_url": dronespot.photo_url,
                "distance": course.distance,
                "duration": course.duration
            })

    accommodations = db.query(PlaceModel).join(DronePlaceModel, DronePlaceModel.place_id == PlaceModel.id).filter(
        DronePlaceModel.dronespot_id == dronespot_id, PlaceModel.place_type_id == 32).order_by(func.random()).limit(
        5).all()

    restaurants = db.query(PlaceModel).join(DronePlaceModel, DronePlaceModel.place_id == PlaceModel.id).filter(
        DronePlaceModel.dronespot_id == dronespot_id, PlaceModel.place_type_id == 39).order_by(func.random()).limit(
        5).all()

    accommodations_data = [{
        "id": place.id,
        "name": place.name,
        "comment": place.comment,
        "photo": place.photo_url,
        "location": {
            "lat": place.lat,
            "lon": place.lon,
            "address": place.address
        },
        "place_type_id": place.place_type_id
    } for place in accommodations]

    restaurants_data = [{
        "id": place.id,
        "name": place.name,
        "comment": place.comment,
        "photo": place.photo_url,
        "location": {
            "lat": place.lat,
            "lon": place.lon,
            "address": place.address
        },
        "place_type_id": place.place_type_id
    } for place in restaurants]

    response_data = {
        "id": dronespot.id,
        "name": dronespot.name,
        "is_like": is_like,
        "location": {"lat": dronespot.lat, "lon": dronespot.lon, "address": dronespot.address},
        "likes_count": likes_count,
        "reviews_count": len(reviews),
        "photo_url": dronespot.photo_url,
        "comment": dronespot.comment,
        "area": [{"id": 1, "name": "Area 1"}, {"id": 2, "name": "Area 2"}],
        "permit": {"flight": dronespot.permit_flight, "camera": dronespot.permit_camera},
        "reviews": review_data,
        "courses": courses,
        "places": {
            "accommodations": accommodations_data,
            "restaurants": restaurants_data
        }
    }

    return response_data