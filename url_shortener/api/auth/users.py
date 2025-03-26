import uuid
from typing import Optional
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, models
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from url_shortener.db import get_user_db, User
from url_shortener.config import AUTH_TOKEN


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = AUTH_TOKEN
    verification_token_secret = AUTH_TOKEN

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        """
        Вызывается после успешной регистрации пользователя.

        Parameters
        ----------
        user : User
            Экземпляр пользователя, который зарегистрировался.
        request : Optional[Request], optional
            Объект HTTP-запроса, по умолчанию None.
        """
        print(f'User {user.id} has registered.')

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """
        Вызывается после запроса пользователем сброса пароля.

        Parameters
        ----------
        user : User
            Экземпляр пользователя, запросившего сброс пароля.
        token : str
            Токен для сброса пароля, сгенерированный для пользователя.
        request : Optional[Request], optional
            Объект HTTP-запроса, по умолчанию None.
        """
        print(f'User {user.id} has forgot their password. Reset token: {token}')

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """
        Вызывается после запроса пользователем верификации email.

        Parameters
        ----------
        user : User
            Экземпляр пользователя, запросившего верификацию.
        token : str
            Токен для верификации, сгенерированный для пользователя.
        request : Optional[Request], optional
            Объект HTTP-запроса, по умолчанию None.
        """
        print(f'Verification requested for user {user.id}. Verification token: {token}')


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    """
    Зависимость для получения экземпляра UserManager.

    Parameters
    ----------
    user_db : SQLAlchemyUserDatabase
        Зависимость базы данных пользователей.

    Returns
    -------
    UserManager
        Экземпляр UserManager.
    """
    yield UserManager(user_db)


def get_jwt_strategy() -> JWTStrategy[models.UP, models.ID]:
    """
    Возвращает стратегию JWT для аутентификации.

    Returns
    -------
    JWTStrategy
        Экземпляр стратегии JWT, настроенный с секретом и временем жизни токена.
    """
    return JWTStrategy(secret=AUTH_TOKEN, lifetime_seconds=3600)


bearer_transport = BearerTransport(tokenUrl='auth/jwt/login')

auth_backend = AuthenticationBackend(
    name='jwt',
    transport=bearer_transport,
    get_strategy=get_jwt_strategy
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
current_active_optional_user = fastapi_users.current_user(
    active=True,
    optional=True
)
