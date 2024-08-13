from fastapi import FastAPI
from api.v1.api import router as api_router
from core.config import settings
from database.mariadb_session import *
from schemas import *
from core.security import *

app = FastAPI()
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