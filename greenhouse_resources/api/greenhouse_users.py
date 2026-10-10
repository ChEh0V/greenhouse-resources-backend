"""Домен пользователей: 3 метода."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from greenhouse_resources.models import GreenhouseUser, get_session
from greenhouse_resources.schemas import GreenhouseUserCredentials, GreenhouseUserOut
from greenhouse_resources.security import hash_password
from greenhouse_resources.singleton import get_current_user_id

router = APIRouter(prefix="/api/greenhouse_users", tags=["Пользователи"])


# ------------------------------------------------------------------ 8. POST регистрация
@router.post("/register", response_model=GreenhouseUserOut, status_code=status.HTTP_201_CREATED)
def register_greenhouse_user(data: GreenhouseUserCredentials,
                             session: Session = Depends(get_session)):
    if session.query(GreenhouseUser).filter(GreenhouseUser.login == data.login).first():
        raise HTTPException(status.HTTP_409_CONFLICT)
    user = GreenhouseUser(login=data.login, password=hash_password(data.password))
    session.add(user)
    session.commit()
    return GreenhouseUserOut(user_id=user.user_id, login=user.login)


# ------------------------------------------------------------------ 9. POST аутентификация
@router.post("/login", response_model=GreenhouseUserOut)
def login_greenhouse_user(data: GreenhouseUserCredentials,
                          session: Session = Depends(get_session),
                          user_id: int = Depends(get_current_user_id)):
    """Заглушка до лабораторной №4: возвращает пользователя-константу."""
    user = session.get(GreenhouseUser, user_id)
    return GreenhouseUserOut(user_id=user.user_id, login=user.login)


# ------------------------------------------------------------------ 10. POST деавторизация
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_greenhouse_user():
    """Заглушка до лабораторной №4."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)
