from fastapi import FastAPI, Request, HTTPException, status, Depends
from jose import JWTError, jwt
from typing import Optional

app = FastAPI()

SECRET_KEY = "dlatlzl" #테스트용 임시키
ALGORITHM = "HS256"

def get_token_from_header(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[len("Bearer "):]
    return None

def get_acc_from_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        acc = payload.get("access")
        if acc is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token does not contain 'acc'")
        return acc
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

async def get_acc_from_request(request: Request) -> str:
    token = get_token_from_header(request)
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header missing or invalid")
    return get_acc_from_token(token)

@app.get("/protected")
async def protected_route(acc: str = Depends(get_acc_from_request)):
    return {"access": acc}
