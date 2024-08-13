from fastapi import APIRouter
from starlette.responses import JSONResponse

router = APIRouter()

@router.post("/logout")
async def logout():
    response = JSONResponse(content={"message": "로그아웃 되었습니다."})
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return response
