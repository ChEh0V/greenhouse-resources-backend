"""
Расчёт требуемых ресурсов для теплицы на Севере.
Лабораторная работа №2: PostgreSQL, SQLAlchemy ORM, шесть HTTP-методов.
"""

from datetime import datetime

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from greenhouse_resources.models import (
    DEFAULT_IMAGE_KEY, DEFAULT_VIDEO_KEY, GreenhouseResource, ResourceLike,
    SessionLocal, STATUS_DELETED, STATUS_DRAFT, STATUS_PUBLISHED, build_minio_url,
)
from greenhouse_resources.seed import init_database

app = FastAPI(title="Ресурсы теплицы на Севере")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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


def with_likes(session, resource):
    """Количество лайков вычисляется запросом к таблице м-м."""
    if resource is None:
        return None
    likes = session.query(func.count(ResourceLike.like_id)).filter(
        ResourceLike.resource_id == resource.resource_id
    ).scalar()
    return {
        "resource_id": resource.resource_id,
        "resource_name": resource.resource_name,
        "short_description": resource.short_description or "",
        "resource_status": resource.resource_status,
        "image_url": resource.image_url or "",
        "video_url": resource.video_url or "",
        "unit": resource.unit or "",
        "min_value": resource.min_value,
        "likes_count": likes,
    }


@app.get("/", response_class=RedirectResponse)
async def root():
    return RedirectResponse(url="/greenhouse_resources/feed")


# ---------------------------------------------------------------- GET 1
@app.get("/greenhouse_resources/feed", response_class=HTMLResponse)
async def resource_feed(request: Request, resource_id: int = 0,
                        next: bool = False, session: Session = Depends(get_session)):
    published = session.query(GreenhouseResource).filter(
        GreenhouseResource.resource_status == STATUS_PUBLISHED
    ).order_by(GreenhouseResource.resource_id).all()

    current = None
    if published:
        if resource_id == 0:
            current = published[0]
        elif next:
            ids = [r.resource_id for r in published]
            position = ids.index(resource_id) if resource_id in ids else -1
            current = published[(position + 1) % len(published)]
        else:
            current = session.query(GreenhouseResource).filter(
                GreenhouseResource.resource_id == resource_id,
                GreenhouseResource.resource_status != STATUS_DELETED,
            ).first()

    return templates.TemplateResponse("feed.html", {
        "request": request,
        "resource": with_likes(session, current),
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
        "resource": with_likes(session, draft),
        "active_tab": "draft",
    })


# ---------------------------------------------------------------- GET 3
@app.get("/greenhouse_resources", response_class=HTMLResponse)
async def resource_grid(request: Request, min_value: float = None,
                        session: Session = Depends(get_session)):
    bounds = session.query(
        func.min(GreenhouseResource.min_value), func.max(GreenhouseResource.min_value)
    ).filter(GreenhouseResource.resource_status == STATUS_PUBLISHED).first()
    slider_min = bounds[0] if bounds[0] is not None else 0.0
    slider_max = bounds[1] if bounds[1] is not None else 100.0

    query = session.query(GreenhouseResource).filter(
        GreenhouseResource.resource_status == STATUS_PUBLISHED
    )
    if min_value is not None:
        query = query.filter(GreenhouseResource.min_value >= min_value)
    resources = query.order_by(GreenhouseResource.resource_id).all()

    return templates.TemplateResponse("grid.html", {
        "request": request,
        "resources": [with_likes(session, r) for r in resources],
        "min_value": min_value if min_value is not None else slider_min,
        "slider_min": slider_min,
        "slider_max": slider_max,
        "active_tab": "grid",
    })


# ---------------------------------------------------------------- POST 1
@app.post("/greenhouse_resources/create")
async def create_resource(resource_name: str = Form(...),
                          session: Session = Depends(get_session)):
    """Создание черновика через ORM. Файлы в БД не сохраняются —
    подставляются изображение и видео по умолчанию."""
    draft = session.query(GreenhouseResource).filter(
        GreenhouseResource.resource_status == STATUS_DRAFT,
        GreenhouseResource.creator_id == CURRENT_USER_ID,
    ).first()

    if draft is None:
        draft = GreenhouseResource(
            resource_name=resource_name,
            resource_status=STATUS_DRAFT,
            image_url=build_minio_url(DEFAULT_IMAGE_KEY),
            video_url=build_minio_url(DEFAULT_VIDEO_KEY),
            created_at=datetime.now(),
            creator_id=CURRENT_USER_ID,
        )
        session.add(draft)
    else:
        draft.resource_name = resource_name

    session.commit()
    return RedirectResponse(url="/greenhouse_resources/draft", status_code=303)


# ---------------------------------------------------------------- POST 2
@app.post("/greenhouse_resources/publish")
async def publish_resource(resource_id: int = Form(...),
                           short_description: str = Form(...),
                           unit: str = Form(...),
                           min_value: float = Form(...),
                           session: Session = Depends(get_session)):
    """Публикация услуги через ORM: смена статуса и заполнение полей по теме."""
    resource = session.query(GreenhouseResource).filter(
        GreenhouseResource.resource_id == resource_id
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
    """Логическое удаление услуги SQL-запросом UPDATE, без использования ORM."""
    session.execute(
        text(
            "UPDATE greenhouse_resources "
            "SET resource_status = :status "
            "WHERE resource_id = :resource_id"
        ),
        {"status": STATUS_DELETED, "resource_id": resource_id},
    )
    session.commit()
    return RedirectResponse(url="/greenhouse_resources", status_code=303)
