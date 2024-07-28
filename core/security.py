from fastapi import FastAPI, Request, HTTPException, status, Depends
from jose import JWTError, jwt
from typing import Optional

app = FastAPI()

SECRET_KEY = "dlatlzl"  # 테스트용 임시키
ALGORITHM = "HS256"


def get_token_from_header(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[len("Bearer "):]
    return None


def get_access_key_from_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        access_key = payload.get("access")
        if access_key is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="'access'정보가 없음")
        return access_key
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")


async def get_access_key_from_request(request: Request) -> str:
    token = get_token_from_header(request)
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header가 없거나 invalid함")
    return get_access_key_from_token(token)

