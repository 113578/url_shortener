from typing import Union
from datetime import datetime, timezone
from celery import Celery
from sqlalchemy import select, insert
from url_shortener.db import (
    sync_session,
    CurrentURLs,
    DeletedURLs
)
from url_shortener.config import REDIS_HOST, REDIS_PORT_CELERY


celery = Celery(
    'delete_expired_links',
    broker=f'redis://{REDIS_HOST}:{REDIS_PORT_CELERY}/0',
    backend=f'redis://{REDIS_HOST}:{REDIS_PORT_CELERY}/0'
)
celery.conf.timezone = 'UTC'


@celery.task(name='delete_expired_links')
def delete_expired_links(alias: str) -> Union[str, None]:
    """
    Удаляет истекший короткий URL и перемещает его в таблицу удаленных URL.

    Parameters
    ----------
    alias : str
        Короткий URL (алиас), который нужно удалить.

    Returns
    -------
    Union[str, None]
        Сообщение об ошибке, если URL уже удален, или None в случае успешного выполнения.
    """
    with sync_session() as session:
        query = select(CurrentURLs).where(CurrentURLs.alias == alias)
        query_result = session.execute(query)
        query_result = query_result.scalar_one_or_none()

        if query_result is None:
            return {
                'detail': 'URL is already deleted!'
            }

        session.execute(
            insert(DeletedURLs).values(
                user_id=query_result.user_id,
                url=query_result.url,
                alias=query_result.alias,
                created_at=query_result.created_at,
                expired_at=datetime
                .now(timezone.utc)
                .replace(tzinfo=None),
                clicks_count=query_result.clicks_count,
                last_clicked_at=query_result.last_clicked_at,
                project_name=query_result.project_name
            )
        )

        session.delete(query_result)
        session.commit()
