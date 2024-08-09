from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import jwt
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def get_payload_info(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_access_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        encoded_jwt = payload.get("encoded_jwt")
        expire = payload.get("expire")
        if encoded_jwt is None or expire is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return encoded_jwt, expire
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password + settings.PASSWORD_SALT, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password + settings.PASSWORD_SALT)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None)-> tuple[str, datetime]:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "sub": data["sub"],
        "level": data["level"]
    })
    encoded_jwt = jwt.encode(to_encode, settings.ACCESS_SECRET_KEY, algorithm=settings.ACCESS_TOKEN_ENCODE_ALGORITHM)
    return encoded_jwt, expire

def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> tuple[str, datetime]:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "sub": data["sub"],
        "level": data["level"]
    })
    encoded_jwt = jwt.encode(to_encode, settings.REFRESH_SECRET_KEY, algorithm=settings.REFRESH_TOKEN_ENCODE_ALGORITHM)
    return encoded_jwt, expire

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
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

def decode_refresh_token(token: str) -> Optional[Dict[str, Any]]:
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
        