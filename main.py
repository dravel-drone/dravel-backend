from fastapi import FastAPI
from api.v1.api import router as api_router
from core.config import settings
from database.mariadb_session import *
from schemas import *
from core.security import *

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from fastapi.staticfiles import StaticFiles

from core.config import settings
from core.scheduler.refresh_manager import delete_expired_refresh

app = FastAPI()
scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup_event():
    print('startup')
    # scheduler.add_job(task, CronTrigger(hour=12, minute=26, timezone='Asia/Seoul'))
    scheduler.add_job(delete_expired_refresh, IntervalTrigger(hours=1, timezone='Asia/Seoul'))
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    print('shudown')
    scheduler.shutdown()

app.mount("/media", StaticFiles(directory=settings.MEDIA_DIR), name="media")

app.include_router(api_router, prefix="/api/v1")



# app.include_router(api_router, prefix=settings.API_V1_STR)

# @app.post("/refresh")
# def refresh_token(token: str, db: Session = Depends(get_db)):
#     db_refresh_token = db.query(Refresh).filter(Refresh.token == token).first()
#     if not db_refresh_token:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid refresh token",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#
#     try:
#         payload = decode_refresh_token(token)
#         username = payload.get("sub")
#         if username is None:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid refresh token",
#                 headers={"WWW-Authenticate": "Bearer"},
#             )
#     except jwt.PyJWTError:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid refresh token",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#
#     access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token, access_expire = create_access_token(data={"sub": username}, expires_delta=access_token_expires)
#
#     return {"access_token": access_token, "token_type": "bearer"}