import hashlib

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from shared.config import settings

security: HTTPBearer = HTTPBearer()


async def has_access(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = hashlib.md5(credentials.credentials.encode("utf-8")).hexdigest()
    if token == settings.app.secret_hash:
        return True
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )