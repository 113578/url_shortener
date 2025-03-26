from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
from db import User, create_db_and_tables
from api import (
    UserCreate,
    UserRead,
    UserUpdate,
    auth_backend,
    current_active_user,
    fastapi_users,
    router_management,
    router_statistics
)
from config import REDIS_HOST


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """
    Контекстный менеджер для управления временем жизни приложения.

    Выполняет создание базы данных и инициализацию кэша Redis.

    Yields
    ------
    None
    """
    await create_db_and_tables()

    redis = aioredis.from_url(f'redis://{REDIS_HOST}')
    FastAPICache.init(RedisBackend(redis), prefix='fastapi-cache')

    yield


app = FastAPI(lifespan=lifespan)

app.include_router(
    router=fastapi_users.get_auth_router(auth_backend),
    prefix='/auth/jwt',
    tags=['auth']
)
app.include_router(
    router=fastapi_users.get_register_router(UserRead, UserCreate),
    prefix='/auth',
    tags=['auth'],
)
app.include_router(
    router=fastapi_users.get_reset_password_router(),
    prefix='/auth',
    tags=['auth'],
)
app.include_router(
    router=fastapi_users.get_verify_router(UserRead),
    prefix='/auth',
    tags=['auth'],
)
app.include_router(
    router=fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix='/users',
    tags=['users'],
)
app.include_router(
    router=router_management,
    prefix='/links',
    tags=['links']
)
app.include_router(
    router=router_statistics,
    prefix='/links',
    tags=['links']
)


@app.get('/authenticated-route')
async def authenticated_route(user: User = Depends(current_active_user)) -> dict:
    """
    Пример защищенного маршрута, доступного только для аутентифицированных пользователей.

    Parameters
    ----------
    user : User
        Текущий аутентифицированный пользователь.

    Returns
    -------
    dict
        Сообщение с приветствием для пользователя.
    """
    return {'message': f'Hello {user.email}!'}


@app.get('/')
async def health_checl() -> dict:
    """
    Проверяет состояние приложения.

    Returns
    -------
    dict
        Сообщение о состоянии приложения.
    """
    return {'message': 'App is healthy!'}
