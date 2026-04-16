import os
from typing import Annotated
from uuid import UUID

import httpx
from dotenv import load_dotenv
from fastapi import Cookie, HTTPException, status


async def get_user_id_from_token(token: Annotated[str | None, Cookie()] = None) -> UUID:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='you are not authenticated')
    async with httpx.AsyncClient() as client:
        try:
            load_dotenv()
            response = await client.post(
                f'{os.getenv("AUTH_SERVICE_URL")}/auth/get_user_id',
                json={'token': token}
            )
            if response.status_code == 422:
                raise HTTPException(status_code=401, detail='you are not authenticated')
            response.raise_for_status()
        except httpx.RequestError as e:
            # если Auth-сервис недоступен, возвращаем 503
            raise HTTPException(status_code=503, detail='Auth service unavailable, please try later')
    return response.json()
