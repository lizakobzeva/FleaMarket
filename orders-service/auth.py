import os
from typing import Annotated, Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)]
) -> int:
    auth_url = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000").rstrip("/")
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="you are not authenticated")
    headers = {"Authorization": f"Bearer {credentials.credentials}"}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{auth_url}/auth/me", headers=headers, timeout=5.0)
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth service unavailable, please try later",
            )

    if resp.status_code == status.HTTP_401_UNAUTHORIZED:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="you are not authenticated")
    if resp.status_code != status.HTTP_200_OK:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="auth service error")

    data = resp.json()
    user_id = data.get("id")
    if not isinstance(user_id, int):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="auth payload missing user id")
    return user_id

