"""
:mod:`container` -- Dependency Injection (DI) контейнер
===================================
.. moduleauthor:: ilya Barinov <i-barinov@it-serv.ru>
"""

import logging

from dependency_injector import containers, providers
from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from ext_kit_shop import __appname__
from ext_kit_shop.utils.logger import StderrHandler, StdoutHandler, get_logger


class Settings(BaseSettings):
    """Настройки приложения"""

    LOG_LEVEL: str = "INFO"

    POSTGRES_USER: str = Field()
    POSTGRES_PASSWORD: str = Field()
    POSTGRES_DB: str = Field()
    POSTGRES_HOST: str = Field()
    POSTGRES_PORT: int = Field()
    JWT_SECRET_KEY: str = Field()

    # API
    COMPANY_ID: int = Field()
    USER_LOGIN: str = Field()
    PASSWORD: str = Field()

    DB_URL: str | None = None

    @field_validator("DB_URL", mode="before")
    def assemble_db_connection(cls, _v: str, values: ValidationInfo) -> str:
        """Собирает URL для подключения к PostgreSQL."""
        return (
            f"postgresql://{values.data['POSTGRES_USER']}:{values.data['POSTGRES_PASSWORD']}@"
            f"{values.data['POSTGRES_HOST']}:{values.data['POSTGRES_PORT']}/{values.data['POSTGRES_DB']}"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )


def setup_logger(log_level: str) -> logging.Logger:
    """Настройка логгера с YAML-форматированием и поддержкой dynamic extra."""
    logger = get_logger(__appname__)
    logger.setLevel(log_level.upper())
    logger.addHandler(StdoutHandler())
    logger.addHandler(StderrHandler())
    return logger


class CommonDI(containers.DeclarativeContainer):
    """Базовый DI-контейнер"""

    settings = providers.Singleton(Settings)
    logger = providers.Singleton(setup_logger, settings.provided.LOG_LEVEL)
