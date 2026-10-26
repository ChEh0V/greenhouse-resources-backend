"""Сериализаторы (Pydantic-схемы) входных и выходных данных API.
Системные поля (ид, статус, создатель, даты) с клиента не принимаются."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ---------- Домен ресурсов теплицы ----------

class GreenhouseResourceCard(BaseModel):
    """Карточка в плитке."""
    resource_id: int
    resource_name: str
    image_url: str
    min_value: Optional[float]
    likes_count: int
    is_creator: Literal[0, 1]


class ResourceAttributeOut(BaseModel):
    """Атрибут ресурса и его значение."""
    attribute_name: str
    attribute_value: str


class GreenhouseResourceFeed(BaseModel):
    """Одна карточка ленты."""
    resource_id: int
    resource_name: str
    short_description: Optional[str]
    image_url: str
    video_url: str
    unit: Optional[str]
    min_value: Optional[float]
    likes_count: int
    is_liked: Literal[0, 1]
    attributes: List[ResourceAttributeOut]


class GreenhouseResourceDraft(BaseModel):
    """Черновик пользователя."""
    resource_id: int
    resource_name: str
    short_description: Optional[str]
    image_url: str
    video_url: str
    unit: Optional[str]
    min_value: Optional[float]


class GreenhouseResourcePublish(BaseModel):
    """Поля, которые заполняются при публикации."""
    short_description: str = Field(min_length=1)
    unit: str = Field(min_length=1, max_length=16)
    min_value: float = Field(ge=0)


class ResourceLikeIn(BaseModel):
    is_liked: Literal[0, 1]


class ResourceLikeOut(BaseModel):
    resource_id: int
    likes_count: int
    is_liked: Literal[0, 1]


# ---------- Домен пользователей ----------

class GreenhouseUserCredentials(BaseModel):
    login: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=64)


class GreenhouseUserOut(BaseModel):
    user_id: int
    login: str
