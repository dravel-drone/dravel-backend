from typing import (
    Dict,
    Any
)

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Response
)
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from models import (
    Course,
    Place,
    CourseVisit,
    Dronespot,
    Review,
    UserDronespotLike
)
from core.auth import verify_user_token
from database.mariadb_session import get_db
from schemas import (
    CourseCreate,
    Course as CourseSchema,
    Dronespot as DronespotSchema,
    Place as PlaceSchema,
    CourseWithPlaces,
    Location,
    Permit
)

router = APIRouter()

def check_admin(
        user_data: Dict[str, Any]
) -> None:
    if user_data is None or not user_data.get("level"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_course_with_places(
        course_id: int,
        db: Session,
        uid=None
):
    course_data = db.query(Course).filter(Course.id == course_id).one()
    visit_data = db.execute(select(CourseVisit).where(CourseVisit.course_id == course_id)).all()
    places = []
    for v in visit_data:
        v = v[0]
        if v.dronespot_id is None:
            place_data = db.query(Place).filter(Place.id == v.place_id).one()
            place_data.area = []
            places.append(PlaceSchema(
                id=place_data.id,
                name=place_data.name,
                comment=place_data.comment,
                photo_url=place_data.photo_url,
                location=Location(
                    lat=place_data.lat,
                    lon=place_data.lon,
                    address=place_data.address,
                ),
                place_type_id=place_data.place_type_id
            ))
        else:
            place_data = db.query(Dronespot).filter(Dronespot.id == v.dronespot_id).one()

            is_like = 0
            if uid is not None:
                like_exist = db.query(UserDronespotLike).filter(
                    UserDronespotLike.user_uid == uid,
                    UserDronespotLike.drone_spot_id == like_exist.id
                ).first()
                if like_exist: is_like = 1

            places.append(DronespotSchema(
                id=place_data.id,
                name=place_data.name,
                photo=place_data.photo_url,
                location=Location(
                    lat=place_data.lat,
                    lon=place_data.lon,
                    address=place_data.address,
                ),
                comment=place_data.comment,
                permit=Permit(
                    flight=place_data.permit_flight,
                    camera=place_data.permit_camera
                ),
                is_like=0 if uid is None else is_like,
                likes_count=db.query(func.count(UserDronespotLike.drone_spot_id)).filter(
                    UserDronespotLike.drone_spot_id == place_data.id
                ).scalar(),
                reviews_count=db.query(func.count(Review.id)).filter(
                    Review.dronespot_id == place_data.id
                ).scalar(),
                area=[]
            ))
    course_data.places = places
    return course_data


@router.post("/course", response_model=CourseSchema, status_code=status.HTTP_200_OK)
async def create_curse(
        course_data: CourseCreate,
        user_data: Dict[str, Any] = Depends(verify_user_token),
        db: Session = Depends(get_db)
):
    check_admin(user_data)

    course_model = Course(
        name=course_data.name,
        content=course_data.content,
        distance=0,
        duration=0
    )
    db.add(course_model)
    db.commit()
    db.refresh(course_model)

    return course_model


@router.delete("/course/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_curse(
        course_id: int,
        user_data: Dict[str, Any] = Depends(verify_user_token),
        db: Session = Depends(get_db)
):
    check_admin(user_data)

    course_exists = db.query(Course).filter(
        Course.id == course_id,
    ).first()

    if not course_exists:
        raise HTTPException(
            status_code=400,
            detail="This course data does not exist",
        )

    db.delete(course_exists)
    db.commit()

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )

@router.post('/course/{course_id}/place/{place_id}', response_model=CourseWithPlaces, status_code=status.HTTP_200_OK)
async def add_place(
        course_id: int,
        place_id: int,
        user_data: Dict[str, Any] = Depends(verify_user_token),
        db: Session = Depends(get_db)
):
    check_admin(user_data)

    course_data = db.query(Course).filter(
        Course.id == course_id
    ).first()
    if not course_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="코스 데이터를 찾을 수 없습니다."
        )

    place_data = db.query(Place).filter(
        Place.id == place_id
    ).first()
    if not place_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="장소 데이터를 찾을 수 없습니다."
        )

    course_visit = CourseVisit(
        course_id=course_data.id,
        place_id=place_data.id
    )
    db.add(course_visit)
    db.commit()
    db.refresh(course_visit)

    return get_course_with_places(course_id, db)

@router.post('/course/{course_id}/dronespot/{dronespot_id}', response_model=CourseWithPlaces, status_code=status.HTTP_200_OK)
async def add_dronespot(
        course_id: int,
        dronespot_id: int,
        user_data: Dict[str, Any] = Depends(verify_user_token),
        db: Session = Depends(get_db)
):
    check_admin(user_data)

    course_data = db.query(Course).filter(
        Course.id == course_id
    ).first()
    if not course_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="코스 데이터를 찾을 수 없습니다."
        )

    dronespot_data = db.query(Dronespot).filter(
        Dronespot.id == dronespot_id
    ).first()
    if not dronespot_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="드론스팟 데이터를 찾을 수 없습니다."
        )

    course_visit = CourseVisit(
        course_id=course_data.id,
        dronespot_id=dronespot_data.id
    )
    db.add(course_visit)
    db.commit()
    db.refresh(course_visit)

    return get_course_with_places(course_id, db)
