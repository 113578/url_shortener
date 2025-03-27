import asyncio
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_cache.decorator import cache
from celery.result import AsyncResult
from url_shortener.celery_app import delete_expired_links
from url_shortener.db import (
    User,
    CurrentURLs,
    DeletedURLs,
    get_async_session
)
from url_shortener.api import current_active_user
from url_shortener.utils import search_url
from url_shortener.config import LIFETIME
from .schemas import URLStatistics


router_statistics = APIRouter()


@router_statistics.get('/{alias}/stats')
@cache(expire=60, namespace='url')
async def get_statistics(
    alias: str,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Получает статистику для указанного короткого URL.

    Parameters
    ----------
    alias : str
        Короткий URL (алиас), для которого требуется статистика.
    user : User
        Текущий активный пользователь.
    session : AsyncSession
        Асинхронная сессия базы данных.

    Returns
    -------
    URLStatistics
        Объект со статистикой URL, включая количество кликов и дату последнего клика.
    """
    # Имитация бурной деятельности для проверки кэша.
    await asyncio.sleep(10)

    url = await search_url(session=session, alias=alias)

    if url is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='URL is not found! Create it first.',
        )
    if url.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Sorry, it`s not your URL!',
        )

    AsyncResult(id=url.celery_task_id).revoke(terminate=True)

    expire_at = url.expire_at + timedelta(seconds=int(LIFETIME))

    celery_task = delete_expired_links.apply_async(
        args=[url.alias],
        eta=url.expire_at,
        expires=3600
    )
    url.celery_task_id = celery_task.id
    url.expire_at = expire_at

    await session.commit()
    await session.refresh(url)

    return URLStatistics(
        url=url.url,
        created_at=url.created_at,
        clicks_count=url.clicks_count,
        last_clicked_at=url.last_clicked_at
    )


@router_statistics.get('/projects/{project_name}')
@cache(expire=60, namespace='url')
async def get_project_name(
    project_name: str,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Получает все текущие URL, связанные с указанным проектом.

    Parameters
    ----------
    project_name : str
        Название проекта для поиска URL.
    user : User
        Текущий активный пользователь.
    session : AsyncSession
        Асинхронная сессия базы данных.

    Returns
    -------
    list
        Список текущих URL, связанных с проектом.
    """
    query = select(CurrentURLs).where(
        and_(
            CurrentURLs.project_name == project_name,
            CurrentURLs.user_id == user.id
        )
    )
    query_result = await session.execute(query)
    query_result = query_result\
        .scalars()\
        .all()

    if not query_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Project {project_name} is not found! Create it first.',
        )

    return query_result


@router_statistics.get('/tools/expired_urls')
@cache(expire=60, namespace='url')
async def get_expired_urls(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Получает список всех истекших URL для текущего пользователя.

    Parameters
    ----------
    user : User
        Текущий активный пользователь.
    session : AsyncSession
        Асинхронная сессия базы данных.

    Returns
    -------
    list
        Список истекших URL.
    """
    query = select(DeletedURLs).where(
        and_(DeletedURLs.user_id == user.id)
    )
    query_result = await session.execute(query)
    query_result = query_result\
        .scalars()\
        .all()

    return query_result
