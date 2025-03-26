from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy import func, DateTime, String, ForeignKey, Text
from fastapi_users.db import SQLAlchemyBaseUserTableUUID


class Base(DeclarativeBase):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )


class CurrentURLs(Base):
    __tablename__ = 'current_urls'

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        nullable=False
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey('user.id'),
        nullable=True
    )
    url: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    alias: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
    expire_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )
    clicks_count: Mapped[int] = mapped_column(
        default=0
    )
    last_clicked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    project_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    celery_task_id: Mapped[int] = mapped_column(
        String(255),
        nullable=False
    )


class DeletedURLs(Base):
    __tablename__ = 'deleted_urls'

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        nullable=False
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey('user.id', ondelete='SET NULL'),
        nullable=True
    )
    url: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    alias: Mapped[str] = mapped_column(
        Text,
        unique=True,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
    expired_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )
    clicks_count: Mapped[int] = mapped_column(
        default=0
    )
    last_clicked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    project_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
