"""Домен ресурсов теплицы (услуг): 7 методов."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from greenhouse_resources.minio_storage import upload_resource_file
from greenhouse_resources.models import (
    GreenhouseResource, ResourceLike, STATUS_DELETED, STATUS_DRAFT, STATUS_PUBLISHED,
    get_session,
)
from greenhouse_resources.schemas import (
    GreenhouseResourceCard, GreenhouseResourceDraft, GreenhouseResourceFeed,
    GreenhouseResourcePublish, ResourceLikeIn, ResourceLikeOut,
)
from greenhouse_resources.singleton import get_current_user_id

router = APIRouter(prefix="/api/greenhouse_resources", tags=["Ресурсы теплицы"])


def likes_count_subquery(session):
    return (
        session.query(func.count(ResourceLike.like_id))
        .filter(ResourceLike.resource_id == GreenhouseResource.resource_id)
        .correlate(GreenhouseResource)
        .scalar_subquery()
    )


def find_draft(session, user_id):
    return session.query(GreenhouseResource).filter(
        GreenhouseResource.resource_status == STATUS_DRAFT,
        GreenhouseResource.creator_id == user_id,
    ).first()


def draft_to_schema(resource):
    return GreenhouseResourceDraft(
        resource_id=resource.resource_id,
        resource_name=resource.resource_name,
        short_description=resource.short_description,
        image_url=resource.image_url,
        video_url=resource.video_url,
        unit=resource.unit,
        min_value=resource.min_value,
    )


# ------------------------------------------------------------------ 1. GET список
@router.get("", response_model=List[GreenhouseResourceCard])
def list_greenhouse_resources(min_value: Optional[float] = None,
                              session: Session = Depends(get_session),
                              user_id: int = Depends(get_current_user_id)):
    """Плитка: опубликованные ресурсы с фильтром по минимальному значению.
    is_creator = 1, если ресурс создан текущим пользователем."""
    query = session.query(GreenhouseResource, likes_count_subquery(session)).filter(
        GreenhouseResource.resource_status == STATUS_PUBLISHED
    )
    if min_value is not None:
        query = query.filter(GreenhouseResource.min_value >= min_value)

    return [
        GreenhouseResourceCard(
            resource_id=resource.resource_id,
            resource_name=resource.resource_name,
            image_url=resource.image_url,
            min_value=resource.min_value,
            likes_count=likes_count,
            is_creator=int(resource.creator_id == user_id),
        )
        for resource, likes_count in query.order_by(GreenhouseResource.resource_id).all()
    ]


# ------------------------------------------------------------------ 2. GET лента
@router.get("/feed", response_model=GreenhouseResourceFeed)
def get_greenhouse_resource_feed(resource_id: Optional[int] = None, next: bool = False,
                                 session: Session = Depends(get_session),
                                 user_id: int = Depends(get_current_user_id)):
    """Лента: одна опубликованная карточка.
    Без resource_id — первая; с ?next=true — следующая после указанной (по кругу).
    is_liked = 1, если текущий пользователь лайкнул эту карточку."""
    is_liked = (
        session.query(func.count(ResourceLike.like_id))
        .filter(ResourceLike.resource_id == GreenhouseResource.resource_id,
                ResourceLike.user_id == user_id)
        .correlate(GreenhouseResource)
        .scalar_subquery()
    )
    published = session.query(
        GreenhouseResource, likes_count_subquery(session), is_liked
    ).filter(
        GreenhouseResource.resource_status == STATUS_PUBLISHED
    ).order_by(GreenhouseResource.resource_id)

    if resource_id is None:
        row = published.first()
    elif next:
        row = published.filter(GreenhouseResource.resource_id > resource_id).first()
        if row is None:
            row = published.first()
    else:
        row = published.filter(GreenhouseResource.resource_id == resource_id).first()

    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    resource, likes_count, liked = row
    return GreenhouseResourceFeed(
        resource_id=resource.resource_id,
        resource_name=resource.resource_name,
        short_description=resource.short_description,
        image_url=resource.image_url,
        video_url=resource.video_url,
        unit=resource.unit,
        min_value=resource.min_value,
        likes_count=likes_count,
        is_liked=int(liked > 0),
    )


# ------------------------------------------------------------------ 3. GET черновик
@router.get("/draft", response_model=GreenhouseResourceDraft)
def get_greenhouse_resource_draft(session: Session = Depends(get_session),
                                  user_id: int = Depends(get_current_user_id)):
    """Черновик текущего пользователя (не более одного)."""
    draft = find_draft(session, user_id)
    if draft is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return draft_to_schema(draft)


# ------------------------------------------------------------------ 4. POST добавление
@router.post("", response_model=GreenhouseResourceDraft, status_code=status.HTTP_201_CREATED)
def create_greenhouse_resource(resource_name: str = Form(..., min_length=1, max_length=128),
                               image: UploadFile = File(...),
                               video: UploadFile = File(...),
                               session: Session = Depends(get_session),
                               user_id: int = Depends(get_current_user_id)):
    """Создание черновика: название + файлы изображения и видео.
    Файлы сохраняются в Minio, их url — в полях image_url и video_url."""
    if find_draft(session, user_id) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT)
    if not (image.content_type or "").startswith("image/") \
            or not (video.content_type or "").startswith("video/"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST)

    draft = GreenhouseResource(
        resource_name=resource_name,
        resource_status=STATUS_DRAFT,
        image_url=upload_resource_file(image, "image"),
        video_url=upload_resource_file(video, "video"),
        created_at=datetime.now(),
        creator_id=user_id,
    )
    session.add(draft)
    session.commit()
    return draft_to_schema(draft)


# ------------------------------------------------------------------ 5. PUT публикация
@router.put("/{resource_id}/publish", response_model=GreenhouseResourceDraft)
def publish_greenhouse_resource(resource_id: int, data: GreenhouseResourcePublish,
                                session: Session = Depends(get_session),
                                user_id: int = Depends(get_current_user_id)):
    """Публикация черновика: заполнение полей по теме, статус draft → published.
    Вернуть ресурс в черновик нельзя."""
    resource = session.query(GreenhouseResource).filter(
        GreenhouseResource.resource_id == resource_id,
        GreenhouseResource.resource_status == STATUS_DRAFT,
        GreenhouseResource.creator_id == user_id,
    ).first()
    if resource is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    resource.short_description = data.short_description
    resource.unit = data.unit
    resource.min_value = data.min_value
    resource.resource_status = STATUS_PUBLISHED
    resource.published_at = datetime.now()
    session.commit()
    return draft_to_schema(resource)


# ------------------------------------------------------------------ 6. DELETE удаление
@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_greenhouse_resource(resource_id: int,
                               session: Session = Depends(get_session),
                               user_id: int = Depends(get_current_user_id)):
    """Логическое удаление (статус deleted). Удалить можно только свой ресурс."""
    resource = session.query(GreenhouseResource).filter(
        GreenhouseResource.resource_id == resource_id,
        GreenhouseResource.resource_status != STATUS_DELETED,
    ).first()
    if resource is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if resource.creator_id != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN)

    resource.resource_status = STATUS_DELETED
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ------------------------------------------------------------------ 7. POST лайк
@router.post("/{resource_id}/like", response_model=ResourceLikeOut)
def like_greenhouse_resource(resource_id: int, data: ResourceLikeIn,
                             session: Session = Depends(get_session),
                             user_id: int = Depends(get_current_user_id)):
    """Лайк от текущего пользователя: is_liked = 1 ставит, 0 снимает."""
    resource = session.query(GreenhouseResource).filter(
        GreenhouseResource.resource_id == resource_id,
        GreenhouseResource.resource_status == STATUS_PUBLISHED,
    ).first()
    if resource is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    like = session.query(ResourceLike).filter(
        ResourceLike.resource_id == resource_id,
        ResourceLike.user_id == user_id,
    ).first()
    if data.is_liked == 1 and like is None:
        session.add(ResourceLike(resource_id=resource_id, user_id=user_id))
    elif data.is_liked == 0 and like is not None:
        session.delete(like)
    session.commit()

    likes_count = session.query(func.count(ResourceLike.like_id)).filter(
        ResourceLike.resource_id == resource_id
    ).scalar()
    return ResourceLikeOut(resource_id=resource_id, likes_count=likes_count,
                           is_liked=data.is_liked)
