"""
:mod:`jwt_helper` -- Хелпер для работы с JWT токенами
===================================
.. moduleauthor:: ilya Barinov <i-barinov@it-serv.ru>
"""

import base64
import datetime
import os
import secrets
from typing import Any

import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 60


class JWTHelper:
    """Хелпер для работы с JWT."""

    _secret_key: str | None = None

    @classmethod
    def _get_secret_key(cls) -> str:
        """Получает секретный ключ из переменных окружения."""
        secret_key = os.getenv("JWT_SECRET_KEY")
        if secret_key is None:
            raise ValueError("Переменная окружения JWT_SECRET_KEY не установлена")
        if cls._secret_key != secret_key:
            cls._secret_key = secret_key
        return cls._secret_key

    @classmethod
    def create_token(cls, data: dict[str, Any]) -> str:
        """Создает JWT-токен."""
        secret_key = cls._get_secret_key()
        to_encode = data.copy()
        expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            days=ACCESS_TOKEN_EXPIRE_DAYS
        )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            payload=to_encode,
            key=secret_key,
            algorithm=ALGORITHM,
        )
        return encoded_jwt

    @classmethod
    def verify_token(
        cls,
        token: str,
    ) -> dict[str, Any] | None:
        """Проверяет JWT-токен."""
        try:
            secret_key = cls._get_secret_key()
            payload = jwt.decode(
                jwt=token,
                key=secret_key,
                algorithms=[ALGORITHM],
            )
            return payload  # type: ignore
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
