import hashlib
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi_cache import FastAPICache
from db import CurrentURLs


def generate_alias(url: str) -> str:
    """
    Генерирует уникальный алиас для указанного URL.

    Parameters
    ----------
    url : str
        Оригинальный URL, для которого нужно создать алиас.

    Returns
    -------
    str
        Сгенерированный алиас длиной 8 символов.
    """
    digest_value = hashlib\
        .sha256(url.encode())\
        .hexdigest()
    alias = ''.join(random.choices(digest_value, k=8))

    return alias


async def search_url(session: AsyncSession, alias: str) -> bool:
    """
    Ищет короткий URL по указанному алиасу.

    Parameters
    ----------
    session : AsyncSession
        Асинхронная сессия базы данных.
    alias : str
        Алиас короткого URL для поиска.

    Returns
    -------
    bool
        Найденный объект URL или None, если URL не найден.
    """
    query = select(CurrentURLs).where(CurrentURLs.alias == alias)
    query_result = await session.execute(query)
    query_result = query_result.scalar_one_or_none()

    return query_result


async def delete_redis_keys(namespace: str) -> None:
    """
    Удаляет все ключи Redis, связанные с указанным пространством имен.

    Parameters
    ----------
    namespace : str
        Пространство имен для удаления ключей.
    """
    redis = FastAPICache\
        .get_backend()\
        .redis
    async for key in redis.scan_iter(f'fastapi-cache:{namespace}:*'):
        await redis.delete(key)
