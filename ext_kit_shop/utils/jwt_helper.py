"""
:mod:`jwt_helper` -- Хелпер для работы с JWT токенами
===================================
.. moduleauthor:: ilya Barinov <i-barinov@it-serv.ru>
"""

import base64
import datetime
import secrets
from typing import Any

import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 60


class JWTHelper:
    """Хелпер для работы с JWT."""

    @staticmethod
    def create_token(data: dict[str, Any], key: str) -> str:
        """Создает JWT-токен."""
        to_encode = data.copy()
        expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            days=ACCESS_TOKEN_EXPIRE_DAYS
        )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            payload=to_encode,
            key=key,
            algorithm=ALGORITHM,
        )
        return encoded_jwt

    @staticmethod
    def verify_token(token: str, key: str) -> dict[str, Any] | None:
        """Проверяет JWT-токен."""
        try:
            payload = jwt.decode(
                jwt=token,
                key=key,
                algorithms=[ALGORITHM],
            )
            return payload  # type: ignore
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    @staticmethod
    def generate_secure_jwt_key() -> str:
        """Генерирует надежный секретный ключ для JWT."""
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8")
