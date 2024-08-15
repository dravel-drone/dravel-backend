import os
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from starlette.staticfiles import StaticFiles

from models import UserDronespotLike, Dronespot as DronespotModel, User as UserModel
from schemas import Dronespot, Permit, Area, Location
from core.auth import verify_user_token
from database.mariadb_session import get_db
from starlette.responses import JSONResponse

router = APIRouter()
MEDIA_DIR = "media"
router.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

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
        save_path = os.path.join(MEDIA_DIR, new_filename)
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
        save_path = os.path.join(MEDIA_DIR, new_filename)
        with open(save_path, "wb") as f:
            f.write(await file.read())
        db_dronespot.photo_url = f"/media/{new_filename}"

    db.commit()
    db.refresh(db_dronespot)

    return Dronespot(
        id=db_dronespot.id,
        name=db_dronespot.name,
        is_like=0,
        location=Location(
            lat=db_dronespot.lat,
            lon=db_dronespot.lon,
            address=db_dronespot.address
        ),
        likes_count=0,
        reviews_count=0,
        photo=db_dronespot.photo_url,
        comment=db_dronespot.comment,
        area=[Area(id=1, name="Area 1"), Area(id=2, name="Area 2")],  # 하드코딩된 값
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