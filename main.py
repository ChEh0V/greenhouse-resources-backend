"""
Расчёт требуемых ресурсов для теплицы на Севере.
Лабораторная работа №3: веб-сервис (REST API) для SPA.
"""

from fastapi import FastAPI

from greenhouse_resources.api import greenhouse_resources, greenhouse_users
from greenhouse_resources.seed import init_database

app = FastAPI(title="Ресурсы теплицы на Севере")
app.include_router(greenhouse_resources.router)
app.include_router(greenhouse_users.router)


@app.on_event("startup")
def on_startup():
    init_database()
