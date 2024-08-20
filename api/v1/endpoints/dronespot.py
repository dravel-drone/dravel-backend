import os
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.staticfiles import StaticFiles

from models import UserDronespotLike, Dronespot as DronespotModel, User as UserModel
from schemas import Dronespot, Permit, Area, Location
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
        permit_camera=permit_camera
    )

    db.add(db_dronespot)
    db.commit()
    db.refresh(db_dronespot)

    photo_url = None
    if file:
        file_extension = os.path.splitext(file.filename)[1]
        new_filename = f"dronespot_{db_dronespot.id}_{name}{file_extension}"
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
        }
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
    }

    for key, value in update_data.items():
        if value is not None:
            setattr(db_dronespot, key, value)

    if file:
        file_extension = os.path.splitext(file.filename)[1]
        new_filename = f"dronespot_{db_dronespot.id}_{db_dronespot.name}{file_extension}"
        save_path = os.path.join(settings.MEDIA_DIR, new_filename)
        with open(save_path, "wb") as f:
            f.write(await file.read())
        db_dronespot.photo_url = f"/media/{new_filename}"

    db.commit()
    db.refresh(db_dronespot)

    is_like = (
        db.query(UserDronespotLike)
        .filter(
            UserDronespotLike.user_uid == user_data["sub"],
            UserDronespotLike.drone_spot_id == dronespot_id
        )
        .count()
    )

    likes_count = db.query(func.count(UserDronespotLike.user_uid)).filter(
        UserDronespotLike.drone_spot_id == dronespot_id).scalar()
    reviews_count = 0

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
        )
    )

@router.post("/like/{dronespot_id}", status_code=204)
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

    like_exists = db.query(UserDronespotLike).filter(
        UserDronespotLike.user_uid == user_uid,
        UserDronespotLike.drone_spot_id == dronespot_id
    ).first()
    if like_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already liked this dronespot"
        )

    new_like = UserDronespotLike(
        user_uid=user_uid,
        drone_spot_id=dronespot_id
    )
    db.add(new_like)
    db.commit()

    return JSONResponse(content={"message": "Liked successfully"})

@router.delete("/like/{dronespot_id}", status_code=204)
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

    like_exists = db.query(UserDronespotLike).filter(
        UserDronespotLike.user_uid == user_uid,
        UserDronespotLike.drone_spot_id == dronespot_id
    ).first()
    if not like_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has not liked this dronespot"
        )

    db.delete(like_exists)
    db.commit()

    return JSONResponse(content={"message": "UnLiked successfully"})

@router.get("/dronespot/popular", response_model=List[Dronespot])
async def get_popular_dronespots(
        page_num: int = Query(1, ge=1),
        size: int = Query(10, ge=1),
        db: Session = Depends(get_db),
        user_data: Optional[Dict[str, Any]] = Depends(verify_user_token)
):
    dronespots_query = db.query(
        DronespotModel,
        func.count(UserDronespotLike.user_uid).label('likes_count')
    ).outerjoin(UserDronespotLike, DronespotModel.id == UserDronespotLike.drone_spot_id) \
     .group_by(DronespotModel.id) \
     .order_by(func.count(UserDronespotLike.user_uid).desc()) \
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
            "is_like": 1 if user_uid and db.query(UserDronespotLike).filter(
                UserDronespotLike.user_uid == user_uid,
                UserDronespotLike.drone_spot_id == dronespot.id
            ).first() else 0,
            "location": {
                "lat": dronespot.lat,
                "lon": dronespot.lon,
                "address": dronespot.address
            },
            "likes_count": likes_count,
            "reviews_count": 0,
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

@router.get("/dronespot/{dronespot_id}", response_model=Dronespot)
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

    likes_count = db.query(func.count(UserDronespotLike.user_uid)).filter(
        UserDronespotLike.drone_spot_id == dronespot_id).scalar()

    is_like = (
        db.query(UserDronespotLike)
        .filter(
            UserDronespotLike.user_uid == user_data["sub"],
            UserDronespotLike.drone_spot_id == dronespot_id
        )
        .count() if user_data and user_data.get("sub") else 0
    )

    # test data
    reviews = [
        {
            "id": 1,
            "writer": {
                "uid": "user_1",
                "name": "John Doe"
            },
            "place_name": "Sample Place",
            "permit": {
                "flight": 1,
                "camera": 1
            },
            "drone_type": "DJI Mavic Air",
            "date": "2024-08-01",
            "comment": "Great spot to fly!",
            "photo": "/media/sample_review_photo.jpg",
            "like_count": 5,
            "is_like": 1
        },
    ]

    courses = [
        {
            "id": 1,
            "name": "Sample Course",
            "content": "This is a great course.",
            "places": [
                {
                    "id": 1,
                    "name": "Sample Place 1",
                    "photo": "/media/sample_place_photo_1.jpg"
                },
                {
                    "id": 2,
                    "name": "Sample Place 2",
                    "photo": "/media/sample_place_photo_2.jpg"
                }
            ],
            "distance": 5000,
            "duration": 60
        }
    ]

    accomodations = [
        {
            "id": 1,
            "name": "Sample Hotel",
            "comment": "Cozy place to stay.",
            "photo": "/media/sample_accommodation_photo.jpg",
            "location": {
                "lat": 37.5665,
                "lon": 126.978,
                "address": "Seoul, South Korea"
            }
        }
    ]

    restaurants = [
        {
            "id": 1,
            "name": "Sample Restaurant",
            "comment": "Delicious food.",
            "photo": "/media/sample_restaurant_photo.jpg",
            "location": {
                "lat": 37.5665,
                "lon": 126.978,
                "address": "Seoul, South Korea"
            }
        }
    ]

    return {
        "id": dronespot.id,
        "name": dronespot.name,
        "is_like": is_like,
        "location": {"lat": dronespot.lat, "lon": dronespot.lon, "address": dronespot.address},
        "likes_count": likes_count,
        "reviews_count": len(reviews),
        "photo": dronespot.photo_url,
        "comment": dronespot.comment,
        "area": [{"id": 1, "name": "Area 1"}, {"id": 2, "name": "Area 2"}],
        "permit": {"flight": dronespot.permit_flight, "camera": dronespot.permit_camera},
        "reviews": reviews,
        "courses": courses,
        "places": {"accomodations": accomodations, "restaurants": restaurants}
    }
