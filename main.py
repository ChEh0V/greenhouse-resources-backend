"""
Расчёт требуемых ресурсов для теплицы на Севере.
Лабораторная работа №4: авторизация через сессии (Redis + куки), Swagger.
"""

from fastapi import FastAPI, Response
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from greenhouse_resources.api import greenhouse_resources, greenhouse_users
from greenhouse_resources.seed import init_database

app = FastAPI(
    title="Ресурсы теплицы на Севере",
    description=(
        "Веб-сервис расчёта ресурсов для выращивания урожая в теплице на Севере.\n\n"
        "Без авторизации доступно только чтение: список ресурсов и лента. "
        "Методы создателя требуют сессию: выполните `POST /api/greenhouse_users/login` — "
        "кука `session_id` установится автоматически."
    ),
    version="4.0",
)


@app.exception_handler(StarletteHTTPException)
async def http_error(request, exc):
    """Ошибки — только стандартный код HTTP, без сообщений в теле ответа."""
    return Response(status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    return Response(status_code=422)


app.include_router(greenhouse_resources.router)
app.include_router(greenhouse_users.router)


@app.on_event("startup")
def on_startup():
    init_database()
