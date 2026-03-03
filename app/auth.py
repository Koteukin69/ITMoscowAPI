from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings

_security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Security(_security)) -> None:
    if credentials.credentials != get_settings().api_token:
        raise HTTPException(status_code=401, detail="Invalid token")
