"""
Расчёт требуемых ресурсов для выращивания урожая в теплице на Севере.
Лабораторная работа №1: FastAPI + Jinja2, без базы данных и без JavaScript.
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from greenhouse_resources.collection import (
    build_minio_url,
    count_likes,
    get_draft_resource,
    get_min_value_bounds,
    get_next_published,
    get_published_resources,
    get_resource_by_id,
)

app = FastAPI(title="Ресурсы теплицы на Севере")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def prepare_resource(resource):
    """Дополняет услугу вычисляемыми полями: url из Minio и количество лайков."""
    if resource is None:
        return None
    prepared = dict(resource)
    prepared["image_url"] = build_minio_url(resource["image_key"])
    prepared["video_url"] = build_minio_url(resource["video_key"])
    prepared["likes_count"] = count_likes(resource)
    return prepared


@app.get("/", response_class=RedirectResponse)
async def root():
    """Открытие приложения ведёт на ленту."""
    return RedirectResponse(url="/greenhouse_resources/feed")


# ---------------------------------------------------------------------------
# Контроллер 1. Лента ресурсов по идентификатору услуги
# ---------------------------------------------------------------------------
@app.get("/greenhouse_resources/feed", response_class=HTMLResponse)
async def resource_feed(request: Request, resource_id: int = 0, next: bool = False):
    published = get_published_resources()

    if resource_id == 0:
        current = published[0] if published else None
    elif next:
        current = get_next_published(resource_id)
    else:
        current = get_resource_by_id(resource_id)

    return templates.TemplateResponse(
        "feed.html",
        {
            "request": request,
            "resource": prepare_resource(current),
            "active_tab": "feed",
        },
    )


# ---------------------------------------------------------------------------
# Контроллер 2. Страница добавления — услуга в статусе черновик
# ---------------------------------------------------------------------------
@app.get("/greenhouse_resources/draft", response_class=HTMLResponse)
async def resource_draft(request: Request):
    return templates.TemplateResponse(
        "draft.html",
        {
            "request": request,
            "resource": prepare_resource(get_draft_resource()),
            "active_tab": "draft",
        },
    )


# ---------------------------------------------------------------------------
# Контроллер 3. Плитка — список всех опубликованных услуг с фильтрацией
# ---------------------------------------------------------------------------
@app.get("/greenhouse_resources", response_class=HTMLResponse)
async def resource_grid(request: Request, min_value: float = None):
    slider_min, slider_max = get_min_value_bounds()
    resources = get_published_resources(min_value=min_value)

    return templates.TemplateResponse(
        "grid.html",
        {
            "request": request,
            "resources": [prepare_resource(r) for r in resources],
            "min_value": min_value if min_value is not None else slider_min,
            "slider_min": slider_min,
            "slider_max": slider_max,
            "active_tab": "grid",
        },
    )
