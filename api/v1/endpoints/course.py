from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from schemas import (
    CourseCreate
)

from typing import (
    Dict,
    Any
)
from core.auth import verify_user_token

router = APIRouter()

@router.post("/course")
async def create_curse(
        course_data: CourseCreate,
        user_data: Dict[str, Any] = Depends(verify_user_token)
):
    if user_data is None or not user_data.get("level"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
            headers={"WWW-Authenticate": "Bearer"},
        )


