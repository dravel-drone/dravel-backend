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
