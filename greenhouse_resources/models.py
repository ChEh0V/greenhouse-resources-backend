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


def get_session():
    """Сессия БД на время одного HTTP-запроса."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

STATUS_DRAFT = "draft"
STATUS_PUBLISHED = "published"
STATUS_DELETED = "deleted"



class GreenhouseUser(Base):
    """Пользователи системы."""
    __tablename__ = "greenhouse_users"

    user_id = Column(Integer, primary_key=True)
    login = Column(String(64), nullable=False, unique=True)
    password = Column(String(128), nullable=False)


class GreenhouseResource(Base):
    """Услуги — виды ресурсов для теплицы."""
    __tablename__ = "greenhouse_resources"

    resource_id = Column(Integer, primary_key=True)
    resource_name = Column(String(128), nullable=False)
    short_description = Column(Text, nullable=True)
    resource_status = Column(String(16), nullable=False, default=STATUS_DRAFT)
    image_url = Column(String(256), nullable=False)
    video_url = Column(String(256), nullable=False)
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



class ResourceAttribute(Base):
    """Атрибуты ресурсов — справочник дополнительных характеристик
    (например «Производитель», «Срок службы»). Набор можно расширять без изменения структуры БД."""
    __tablename__ = "resource_attributes"

    attribute_id = Column(Integer, primary_key=True)
    attribute_name = Column(String(64), nullable=False, unique=True)


class ResourceAttributeValue(Base):
    """Вертикальная таблица значений атрибутов — м-м между ресурсами и атрибутами."""
    __tablename__ = "resource_attribute_values"
    __table_args__ = (UniqueConstraint("resource_id", "attribute_id"),)

    value_id = Column(Integer, primary_key=True)
    resource_id = Column(
        Integer,
        ForeignKey("greenhouse_resources.resource_id", ondelete="RESTRICT"),
        nullable=False,
    )
    attribute_id = Column(
        Integer,
        ForeignKey("resource_attributes.attribute_id", ondelete="RESTRICT"),
        nullable=False,
    )
    attribute_value = Column(String(128), nullable=False)
