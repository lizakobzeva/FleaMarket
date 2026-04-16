from http.client import HTTPException
from uuid import UUID, uuid4

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title='Auth service',
    description='Сервис для аутентификации',
    version='1.0.0'
)


class CheckTokenBody(BaseModel):
    token: str


@app.post('/auth/get_user_id')
def get_user_id(token: CheckTokenBody) -> UUID:
    return uuid4()
