"""Домен пользователей: 3 метода."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from greenhouse_resources.auth import (
    SESSION_COOKIE, SESSION_TTL_SECONDS, create_session, delete_session,
    get_current_user_id, session_cookie,
)
from greenhouse_resources.models import GreenhouseUser, get_session
from greenhouse_resources.schemas import GreenhouseUserCredentials, GreenhouseUserOut
from greenhouse_resources.security import hash_password, verify_password

router = APIRouter(prefix="/api/greenhouse_users", tags=["Пользователи"])


# ------------------------------------------------------------------ 8. POST регистрация
@router.post("/register", response_model=GreenhouseUserOut, status_code=status.HTTP_201_CREATED,
             summary="Регистрация")
def register_greenhouse_user(data: GreenhouseUserCredentials,
                             session: Session = Depends(get_session)):
    if session.query(GreenhouseUser).filter(GreenhouseUser.login == data.login).first():
        raise HTTPException(status.HTTP_409_CONFLICT)
    user = GreenhouseUser(login=data.login, password=hash_password(data.password))
    session.add(user)
    session.commit()
    return GreenhouseUserOut(user_id=user.user_id, login=user.login)


# ------------------------------------------------------------------ 9. POST аутентификация
@router.post("/login", response_model=GreenhouseUserOut, summary="Аутентификация")
def login_greenhouse_user(data: GreenhouseUserCredentials, response: Response,
                          session: Session = Depends(get_session)):
    """Проверка логина и пароля. Сессия создаётся в Redis,
    её ид возвращается в куке session_id (httpOnly)."""
    user = session.query(GreenhouseUser).filter(GreenhouseUser.login == data.login).first()
    if user is None or not verify_password(data.password, user.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)

    session_id = create_session(user.user_id, user.login)
    response.set_cookie(SESSION_COOKIE, session_id, max_age=SESSION_TTL_SECONDS,
                        httponly=True, samesite="lax")
    return GreenhouseUserOut(user_id=user.user_id, login=user.login)


# ------------------------------------------------------------------ 10. POST деавторизация
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Деавторизация")
def logout_greenhouse_user(user_id: int = Depends(get_current_user_id),
                           session_id: Optional[str] = Depends(session_cookie)):
    """Удаление сессии из Redis и куки из браузера."""
    delete_session(session_id)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(SESSION_COOKIE)
    return response
