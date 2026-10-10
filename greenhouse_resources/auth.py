"""Авторизация через сессии: ид сессии хранится в куке session_id,
сама сессия — в Redis под ключом session:<ид> со сроком жизни 1 час."""

import json
import os
import uuid
from typing import Optional

import redis
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyCookie

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

SESSION_COOKIE = "session_id"
SESSION_TTL_SECONDS = 3600

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Схема безопасности для Swagger: кнопка Authorize с кукой session_id
session_cookie = APIKeyCookie(name=SESSION_COOKIE, auto_error=False)


def create_session(user_id: int, login: str) -> str:
    session_id = uuid.uuid4().hex
    redis_client.setex(
        f"session:{session_id}", SESSION_TTL_SECONDS,
        json.dumps({"user_id": user_id, "login": login}),
    )
    return session_id


def delete_session(session_id: str) -> None:
    redis_client.delete(f"session:{session_id}")


def find_session_user_id(session_id: Optional[str]) -> Optional[int]:
    if not session_id:
        return None
    data = redis_client.get(f"session:{session_id}")
    return json.loads(data)["user_id"] if data else None


def get_optional_user_id(request: Request) -> Optional[int]:
    """Для методов гостя (чтение): ид пользователя из сессии или None.
    В Swagger эти методы не требуют авторизации."""
    return find_session_user_id(request.cookies.get(SESSION_COOKIE))


def get_current_user_id(session_id: Optional[str] = Depends(session_cookie)) -> int:
    """Для методов создателя: без действующей сессии — 401."""
    user_id = find_session_user_id(session_id)
    if user_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    return user_id
