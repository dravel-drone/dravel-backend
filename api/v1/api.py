from fastapi import APIRouter

from api.v1.endpoints import test, terms, register

# api_router = APIRouter()
# api_router.include_router(test.router, prefix="/test", tags=["test"])

router = APIRouter()
router.include_router(terms.router)
router.include_router(register.router)
