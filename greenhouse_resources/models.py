"""Модели базы данных и подключение к PostgreSQL."""

import os
from datetime import datetime

from sqlalchemy import (
    Column, DateTime, Float, ForeignKey, Integer, String, Text,
    UniqueConstraint, create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://greenhouse:greenhouse@localhost:5433/greenhouse_db",
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()

STATUS_DRAFT = "draft"
STATUS_PUBLISHED = "published"
STATUS_DELETED = "deleted"

DEFAULT_IMAGE_KEY = "default_resource.jpg"
DEFAULT_VIDEO_KEY = "default_resource.mp4"
MINIO_BASE_URL = "http://localhost:9000/greenhouse"


class GreenhouseUser(Base):
    """Пользователи системы."""
    __tablename__ = "greenhouse_users"

    user_id = Column(Integer, primary_key=True)
    login = Column(String(64), nullable=False, unique=True)
    full_name = Column(String(128), nullable=False)
    is_agronomist = Column(Integer, nullable=False, default=0)


class GreenhouseResource(Base):
    """Услуги — виды ресурсов для теплицы."""
    __tablename__ = "greenhouse_resources"

    resource_id = Column(Integer, primary_key=True)
    resource_name = Column(String(128), nullable=False)
    short_description = Column(Text, nullable=True)
    resource_status = Column(String(16), nullable=False, default=STATUS_DRAFT)
    image_url = Column(String(256), nullable=True)
    video_url = Column(String(256), nullable=True)
    # два поля по предметной области
    unit = Column(String(16), nullable=True)
    min_value = Column(Float, nullable=True)
    # системные поля
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    published_at = Column(DateTime, nullable=True)
    creator_id = Column(
        Integer,
        ForeignKey("greenhouse_users.user_id", ondelete="RESTRICT"),
        nullable=False,
    )


class ResourceLike(Base):
    """Лайки — связь многие-ко-многим между пользователями и ресурсами."""
    __tablename__ = "resource_likes"
    __table_args__ = (UniqueConstraint("user_id", "resource_id"),)

    like_id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey("greenhouse_users.user_id", ondelete="RESTRICT"),
        nullable=False,
    )
    resource_id = Column(
        Integer,
        ForeignKey("greenhouse_resources.resource_id", ondelete="RESTRICT"),
        nullable=False,
    )


def build_minio_url(file_key):
    return f"{MINIO_BASE_URL}/{file_key}" if file_key else ""
