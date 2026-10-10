"""
Расчёт требуемых ресурсов для теплицы на Севере.
Лабораторная работа №2: PostgreSQL, SQLAlchemy ORM, шесть HTTP-методов.
"""

from datetime import datetime

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from greenhouse_resources.models import (
    DEFAULT_IMAGE_URL, DEFAULT_VIDEO_URL, GreenhouseResource, ResourceLike,
    SessionLocal, STATUS_DELETED, STATUS_DRAFT, STATUS_PUBLISHED, build_minio_url,
)
from greenhouse_resources.seed import init_database

app = FastAPI(title="Ресурсы теплицы на Севере")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
templates.env.globals.update(
    default_image_url=DEFAULT_IMAGE_URL,
    default_video_url=DEFAULT_VIDEO_URL,
)

CURRENT_USER_ID = 2


@app.on_event("startup")
def on_startup():
    init_database()


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def resources_with_likes(session):
    """Услуги вместе с количеством лайков: подзапрос к таблице м-м в той же строке."""
    return session.query(
        GreenhouseResource,
        session.query(func.count(ResourceLike.like_id))
        .filter(ResourceLike.resource_id == GreenhouseResource.resource_id)
        .correlate(GreenhouseResource)
        .scalar_subquery()
        .label("likes_count"),
    )


@app.get("/", response_class=RedirectResponse)
async def root():
    return RedirectResponse(url="/greenhouse_resources/feed")


# ---------------------------------------------------------------- GET 1
@app.get("/greenhouse_resources/feed", response_class=HTMLResponse)
async def resource_feed(request: Request, resource_id: int = 0,
                        next: bool = False, session: Session = Depends(get_session)):
    """Лента. Из БД всегда возвращается не более одной строки (LIMIT 1)."""
    published = resources_with_likes(session).filter(
        GreenhouseResource.resource_status == STATUS_PUBLISHED
    ).order_by(GreenhouseResource.resource_id)

    if resource_id == 0:
        row = published.first()
    elif next:
        row = published.filter(GreenhouseResource.resource_id > resource_id).first()
        if row is None:
            # после последней карточки лента начинается сначала
            row = published.first()
    else:
        row = published.filter(GreenhouseResource.resource_id == resource_id).first()

    return templates.TemplateResponse("feed.html", {
        "request": request,
        "resource": row[0] if row else None,
        "likes_count": row[1] if row else 0,
        "active_tab": "feed",
    })


# ---------------------------------------------------------------- GET 2
@app.get("/greenhouse_resources/draft", response_class=HTMLResponse)
async def resource_draft(request: Request, session: Session = Depends(get_session)):
    draft = session.query(GreenhouseResource).filter(
        GreenhouseResource.resource_status == STATUS_DRAFT,
        GreenhouseResource.creator_id == CURRENT_USER_ID,
    ).first()

    return templates.TemplateResponse("draft.html", {
        "request": request,
        "resource": draft,
        "active_tab": "draft",
    })


# ---------------------------------------------------------------- GET 3
@app.get("/greenhouse_resources", response_class=HTMLResponse)
async def resource_grid(request: Request, min_value: str = "",
                        session: Session = Depends(get_session)):
    """Плитка с фильтрацией на сервере по минимальному значению ресурса.
    Пустое поле фильтра — показываются все опубликованные ресурсы."""
    query = resources_with_likes(session).filter(
        GreenhouseResource.resource_status == STATUS_PUBLISHED
    )
    if min_value.strip():
        query = query.filter(GreenhouseResource.min_value >= float(min_value))
    rows = query.order_by(GreenhouseResource.resource_id).all()

    return templates.TemplateResponse("grid.html", {
        "request": request,
        "rows": rows,
        "min_value": min_value,
        "active_tab": "grid",
    })


# ---------------------------------------------------------------- POST 1
@app.post("/greenhouse_resources/create")
async def create_resource(resource_name: str = Form(...),
                          session: Session = Depends(get_session)):
    """Создание черновика через ORM по кнопке «Далее».
    Файлы в этой лабораторной на сервер не передаются — в таблицу записываются
    неверные url, поэтому в интерфейсе показываются фото и видео по умолчанию."""
    draft = session.query(GreenhouseResource).filter(
        GreenhouseResource.resource_status == STATUS_DRAFT,
        GreenhouseResource.creator_id == CURRENT_USER_ID,
    ).first()

    if draft is None:
        file_key = f"new_resource_{int(datetime.now().timestamp())}"
        session.add(GreenhouseResource(
            resource_name=resource_name,
            resource_status=STATUS_DRAFT,
            image_url=build_minio_url(f"{file_key}.jpg"),
            video_url=build_minio_url(f"{file_key}.mp4"),
            created_at=datetime.now(),
            creator_id=CURRENT_USER_ID,
        ))
        session.commit()

    return RedirectResponse(url="/greenhouse_resources/draft", status_code=303)


# ---------------------------------------------------------------- POST 2
@app.post("/greenhouse_resources/publish")
async def publish_resource(resource_id: int = Form(...),
                           short_description: str = Form(...),
                           unit: str = Form(...),
                           min_value: float = Form(...),
                           session: Session = Depends(get_session)):
    """Публикация через ORM: заполнение полей по теме и смена статуса."""
    resource = session.query(GreenhouseResource).filter(
        GreenhouseResource.resource_id == resource_id,
        GreenhouseResource.resource_status == STATUS_DRAFT,
        GreenhouseResource.creator_id == CURRENT_USER_ID,
    ).first()

    if resource is not None:
        resource.short_description = short_description
        resource.unit = unit
        resource.min_value = min_value
        resource.resource_status = STATUS_PUBLISHED
        resource.published_at = datetime.now()
        session.commit()

    return RedirectResponse(url="/greenhouse_resources", status_code=303)


# ---------------------------------------------------------------- POST 3
@app.post("/greenhouse_resources/delete")
async def delete_resource(resource_id: int = Form(...),
                          session: Session = Depends(get_session)):
    """Логическое удаление через SQL-курсор (UPDATE), без ORM."""
    connection = session.connection().connection  # соединение psycopg2
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE greenhouse_resources SET resource_status = %s WHERE resource_id = %s",
        (STATUS_DELETED, resource_id),
    )
    cursor.close()
    session.commit()
    return RedirectResponse(url="/greenhouse_resources", status_code=303)
