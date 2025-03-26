from typing import AsyncGenerator
from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from url_shortener.config import ASYNC_DATABASE_URL, SYNC_DATABASE_URL
from .models import Base, User


async_engine = create_async_engine(ASYNC_DATABASE_URL)
async_session = async_sessionmaker(async_engine, expire_on_commit=False)
sync_engine = create_engine(SYNC_DATABASE_URL)
sync_session = sessionmaker(sync_engine, expire_on_commit=False)


async def create_db_and_tables():
    """
    Создает базу данных и все таблицы, определенные в модели.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Предоставляет асинхронную сессию базы данных.

    Returns
    -------
    AsyncGenerator[AsyncSession, None]
        Генератор асинхронной сессии базы данных.
    """
    async with async_session() as session:
        yield session


async def get_user_db(
        session: AsyncSession = Depends(get_async_session)
) -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
    """
    Предоставляет объект базы данных пользователей.

    Parameters
    ----------
    session : AsyncSession
        Асинхронная сессия базы данных.

    Returns
    -------
    AsyncGenerator[SQLAlchemyUserDatabase, None]
        Генератор базы данных пользователей.
    """
    yield SQLAlchemyUserDatabase(session, User)
