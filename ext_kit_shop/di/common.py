"""
:mod:`container` -- Dependency Injection (DI) контейнер
===================================
.. moduleauthor:: ilya Barinov <i-barinov@it-serv.ru>
"""

import logging
from typing import Any

import yaml
from dependency_injector import containers, providers
from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.console import Console
from rich.syntax import Syntax

from ext_kit_shop import __appname__


class Settings(BaseSettings):
    """Настройки приложения"""

    LOG_LEVEL: str = "INFO"

    POSTGRES_USER: str = Field()
    POSTGRES_PASSWORD: str = Field()
    POSTGRES_DB: str = Field()
    POSTGRES_HOST: str = Field()
    POSTGRES_PORT: int = Field()

    DB_URL: str | None = None

    @field_validator("DB_URL", mode="before")
    @staticmethod
    def assemble_db_connection(_v: str, values: ValidationInfo) -> str:
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


class SensitiveFormatter(logging.Formatter):
    """Форматтер логов в YAML с исключением ненужных полей."""

    EXCLUDED_KEYS = {  # noqa: RUF012
        "args",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "levelno",
        "module",
        "msecs",
        "msg",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "lineno",
        "logger",
        "file",
        "function",
        "levelname",
        "taskName",
    }

    console = Console()

    def format(self, record: logging.LogRecord) -> Any:  # noqa: D102
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key not in self.EXCLUDED_KEYS and not key.startswith("_"):
                try:
                    yaml.dump(value)
                    log_entry[key] = value
                except Exception:  # noqa: BLE001
                    log_entry[key] = str(value)

        yaml_text = yaml.dump(log_entry, default_flow_style=False, allow_unicode=True)
        syntax = Syntax(yaml_text, "yaml", theme="monokai", line_numbers=False)
        self.console.print(syntax)

        return ""


def setup_logger(log_level: str) -> logging.Logger:
    """Настройка логгера с YAML-форматированием и поддержкой dynamic extra."""
    logger = logging.getLogger(__appname__)
    logger.setLevel(log_level.upper())

    handler = logging.StreamHandler()
    handler.setFormatter(SensitiveFormatter())

    logger.addHandler(handler)
    return logger


class CommonDI(containers.DeclarativeContainer):
    """Базовый DI-контейнер"""

    settings = providers.Singleton(Settings)
    logger = providers.Singleton(setup_logger, settings.provided.LOG_LEVEL)
