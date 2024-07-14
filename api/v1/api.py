from fastapi import APIRouter

from api.v1.endpoints import test

api_router = APIRouter()
api_router.include_router(test.router, prefix="/test", tags=["test"])