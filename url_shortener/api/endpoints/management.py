from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_cache.decorator import cache
from celery.result import AsyncResult
from url_shortener.api import (
    current_active_user,
    current_active_optional_user
)
from url_shortener.celery_app import delete_expired_links
from url_shortener.db import (
    User,
    CurrentURLs,
    DeletedURLs,
    get_async_session
)
from url_shortener.utils import (
    generate_alias,
    search_url,
    delete_redis_keys
)
from .schemas import CreateURL, UpdateURL


router_management = APIRouter()


@router_management.post('/shorten')
async def shorten(
    url: CreateURL,
    response: Response,
    user: Optional[User] = Depends(current_active_optional_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Укорачивает URL и сохраняет его в базе данных.

    Parameters
    ----------
    url : CreateURL
        Данные для создания короткого URL.
    response : Response
        Объект ответа HTTP.
    user : Optional[User], optional
        Текущий пользователь, по умолчанию None.
    session : AsyncSession
        Асинхронная сессия базы данных.

    Returns
    -------
    dict
        Информация о созданном коротком URL.
    """
    if url.alias == 'search':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alias 'search' is not allowed! Try another one.",
        )

    if url.alias is None:
        alias = generate_alias(url.url)
        while await search_url(session, url.alias):
            alias = generate_alias
        url.alias = alias

    else:
        if await search_url(session, url.alias):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Alias '{url.alias}' already exists! Try another one.",
            )

    if not url.url.startswith('https'):
        url.url = 'https://' + url.url

    user_id = user if user is None else user.id

    expire_at = datetime\
        .now(timezone.utc)\
        .replace(tzinfo=None)\
        + timedelta(seconds=url.lifetime)

    celery_task = delete_expired_links.apply_async(
        args=[url.alias],
        eta=expire_at,
        expires=3600
    )

    shorten_url = CurrentURLs(
        url=url.url,
        alias=url.alias,
        expire_at=expire_at,
        user_id=user_id,
        project_name=url.project_name,
        celery_task_id=celery_task.id
    )

    session.add(shorten_url)
    await session.commit()
    await session.refresh(shorten_url)

    response.status_code = status.HTTP_201_CREATED
    return {
        'status': 'URL has been shortened!',
        'original_url': shorten_url.url,
        'alias': shorten_url.alias
    }


@router_management.get('/{alias}')
@cache(expire=60, namespace='url')
async def redirect(
    alias: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Перенаправляет на оригинальный URL по его алиасу.

    Parameters
    ----------
    alias : str
        Алиас короткого URL.
    session : AsyncSession
        Асинхронная сессия базы данных.

    Returns
    -------
    RedirectResponse
        Перенаправление на оригинальный URL.
    """
    url = await search_url(session=session, alias=alias)

    if url is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Alias is not found! Create it first.',
        )

    url.clicks_count += 1
    url.last_clicked_at = datetime\
        .now(timezone.utc)\
        .replace(tzinfo=None)

    AsyncResult(id=url.celery_task_id).revoke(terminate=True)

    celery_task = delete_expired_links.apply_async(
        args=[url.alias],
        eta=url.expire_at
    )
    url.celery_task_id = celery_task.id

    await session.commit()
    await session.refresh(url)

    return RedirectResponse(url.url, status_code=307)


@router_management.put('/{alias}')
async def update(
    alias: str,
    updated_url: UpdateURL,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Обновляет оригинальный URL по его алиасу.

    Parameters
    ----------
    alias : str
        Алиас короткого URL.
    updated_url : UpdateURL
        Новые данные для обновления URL.
    user : User
        Текущий пользователь.
    session : AsyncSession
        Асинхронная сессия базы данных.

    Returns
    -------
    dict
        Информация об обновленном URL.
    """
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

    if not updated_url.update_url.startswith('https'):
        updated_url.update_url = 'https://' + updated_url.update_url

    url.url = updated_url.update_url

    AsyncResult(id=url.celery_task_id).revoke(terminate=True)

    celery_task = delete_expired_links.apply_async(
        args=[url.alias],
        eta=url.expire_at,
        expires=3600
    )
    url.celery_task_id = celery_task.id

    await session.commit()
    await session.refresh(url)

    await delete_redis_keys(namespace='url')

    return {
        'detail': 'URL is updated!',
        'updated_url': url.url,
    }


@router_management.delete('/delete/{alias}')
async def delete(
    alias: str,
    user: Optional[User] = Depends(current_active_optional_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Удаляет короткий URL по его алиасу.

    Parameters
    ----------
    alias : str
        Алиас короткого URL.
    user : Optional[User], optional
        Текущий пользователь, по умолчанию None.
    session : AsyncSession
        Асинхронная сессия базы данных.

    Returns
    -------
    Response
        Ответ с кодом 204 при успешном удалении.
    """
    url = await search_url(session=session, alias=alias)
    user_id = user if user is None else user.id

    if url is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='URL is not found! Create it first.',
        )
    if url.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Sorry, it`s not your URL!',
        )

    await session.execute(
        insert(DeletedURLs).values(
            user_id=url.user_id,
            url=url.url,
            alias=url.alias,
            created_at=url.created_at,
            expired_at=datetime
            .now(timezone.utc)
            .replace(tzinfo=None),
            clicks_count=url.clicks_count,
            last_clicked_at=url.last_clicked_at,
            project_name=url.project_name
        )
    )

    AsyncResult(id=url.celery_task_id).revoke(terminate=True)

    await session.delete(url)
    await session.commit()

    await delete_redis_keys(namespace='url')

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


@router_management.get('/tools/search')
@cache(expire=60, namespace='url')
async def search(
    original_url: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Ищет короткие URL, связанные с оригинальным URL.

    Parameters
    ----------
    original_url : str
        Оригинальный URL для поиска.
    session : AsyncSession
        Асинхронная сессия базы данных.

    Returns
    -------
    list
        Список найденных коротких URL.
    """
    if not original_url.startswith('https'):
        original_url = 'https://' + original_url

    query = select(CurrentURLs).where(CurrentURLs.url == original_url)
    query_result = await session.execute(query)
    query_result = query_result\
        .scalars()\
        .all()

    return query_result
