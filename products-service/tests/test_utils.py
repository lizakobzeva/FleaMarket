import asyncio
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.utils import get_current_user_id


class _FakeResp:
    def __init__(self, status_code: int, payload: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


def test_get_current_user_id_no_credentials():
    async def _():
        with pytest.raises(HTTPException) as exc:
            await get_current_user_id(None)
        assert exc.value.status_code == 401

    asyncio.run(_())


def test_get_current_user_id_auth_returns_401():
    async def _():
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="tok")
        with patch("app.utils.httpx.AsyncClient") as mock_cls:
            ctx = AsyncMock()
            ctx.get.return_value = _FakeResp(401)
            mock_cls.return_value.__aenter__.return_value = ctx
            with pytest.raises(HTTPException) as exc:
                await get_current_user_id(creds)
        assert exc.value.status_code == 401

    asyncio.run(_())


def test_get_current_user_id_auth_unavailable():
    async def _():
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="tok")
        with patch("app.utils.httpx.AsyncClient") as mock_cls:
            ctx = AsyncMock()
            ctx.get.side_effect = httpx.RequestError("offline", request=None)
            mock_cls.return_value.__aenter__.return_value = ctx
            with pytest.raises(HTTPException) as exc:
                await get_current_user_id(creds)
        assert exc.value.status_code == 503

    asyncio.run(_())


def test_get_current_user_id_auth_bad_gateway():
    async def _():
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="tok")
        with patch("app.utils.httpx.AsyncClient") as mock_cls:
            ctx = AsyncMock()
            ctx.get.return_value = _FakeResp(500)
            mock_cls.return_value.__aenter__.return_value = ctx
            with pytest.raises(HTTPException) as exc:
                await get_current_user_id(creds)
        assert exc.value.status_code == 502

    asyncio.run(_())


def test_get_current_user_id_missing_id_in_payload():
    async def _():
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="tok")
        with patch("app.utils.httpx.AsyncClient") as mock_cls:
            ctx = AsyncMock()
            ctx.get.return_value = _FakeResp(200, {"email": "a@b.c"})
            mock_cls.return_value.__aenter__.return_value = ctx
            with pytest.raises(HTTPException) as exc:
                await get_current_user_id(creds)
        assert exc.value.status_code == 502

    asyncio.run(_())


def test_get_current_user_id_success():
    async def _():
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="tok")
        with patch("app.utils.httpx.AsyncClient") as mock_cls:
            ctx = AsyncMock()
            ctx.get.return_value = _FakeResp(200, {"id": 42, "email": "a@b.c"})
            mock_cls.return_value.__aenter__.return_value = ctx
            uid = await get_current_user_id(creds)
        assert uid == 42

    asyncio.run(_())
