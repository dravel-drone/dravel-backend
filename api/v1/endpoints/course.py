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

from models import Course
from core.auth import verify_user_token
from database.mariadb_session import get_db
from schemas import (
    CourseCreate,
    Course as CourseModel
)

router = APIRouter()

@router.post("/course", response_model=CourseModel, status_code=status.HTTP_200_OK)
async def create_curse(
        course_data: CourseCreate,
        user_data: Dict[str, Any] = Depends(verify_user_token),
        db: Session = Depends(get_db)
):
    if user_data is None or not user_data.get("level"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
            headers={"WWW-Authenticate": "Bearer"},
        )

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
    if user_data is None or not user_data.get("level"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
            headers={"WWW-Authenticate": "Bearer"},
        )

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
