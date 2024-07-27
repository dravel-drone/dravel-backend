from datetime import datetime, timedelta
from typing import Optional
import jwt
from core.config import settings

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None)-> tuple[str, datetime]:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.ACCESS_SECRET_KEY, algorithm=settings.ACCESS_TOKEN_ENCODE_ALGORITHM)
    return encoded_jwt, expire

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> tuple[str, datetime]:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.REFRESH_SECRET_KEY, algorithm=settings.REFRESH_TOKEN_ENCODE_ALGORITHM)
    return encoded_jwt, expire

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.ACCESS_SECRET_KEY, algorithms=[settings.ACCESS_TOKEN_ENCODE_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        print("Token has expired")
        return None
    except jwt.InvalidTokenError:
        print("Invalid token")
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

def decode_refresh_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.REFRESH_SECRET_KEY, algorithms=[settings.REFRESH_TOKEN_ENCODE_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        print("Token has expired")
        return None
    except jwt.InvalidTokenError:
        print("Invalid token")
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e