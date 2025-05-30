from fastapi import APIRouter


from api.v1.endpoints import test, terms, register, login, logout, dronespot, refresh, review, course, follow, profile, \
    userInfo

# api_router = APIRouter()
# api_router.include_router(test.router, prefix="/test", tags=["test"])

router = APIRouter()
router.include_router(terms.router)
router.include_router(register.router)
router.include_router(login.router)
router.include_router(logout.router)
router.include_router(refresh.router)
router.include_router(dronespot.router)
router.include_router(review.router)
router.include_router(course.router)
router.include_router(follow.router)
router.include_router(profile.router)
router.include_router(userInfo.router)