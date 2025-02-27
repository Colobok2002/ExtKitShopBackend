"""
:mod:`common` -- Базовый класс для создания rout
===================================
.. moduleauthor:: ilya Barinov <i-barinov@it-serv.ru>
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import Enum
from logging import Logger, getLogger
from typing import Any

from fastapi import APIRouter

from ext_kit_shop.models.request import BadResponse, GoodResponse
from ext_kit_shop.utils.db_helper import DBHelper


class RoutsCommon(ABC):
    """Абстрактный класс для rout"""

    def __init__(
        self,
        db_helper: DBHelper,
        prefix: str = "",
        tags: list[str | Enum] | None = None,
        logger: Logger | None = None,
    ):
        """
        :param prefix: Префикс для всех маршрутов в этом роутере.
        :param tags: Теги, используемые для группировки маршрутов в документации.
        """
        self._router = APIRouter(prefix=prefix, tags=tags)
        self.logger = logger or getLogger(__name__)
        self.db_helper = db_helper

    def add_route(self, path: str, endpoint: Callable[..., Any], method: str = "GET") -> None:
        """
        Добавляет маршрут в роутер.

        :param path: URL-путь маршрута.
        :param endpoint: Функция-обработчик запроса.
        :param method: HTTP-метод (GET, POST и т. д.).
        """
        self._router.add_api_route(path, endpoint, methods=[method])

    @abstractmethod
    def setup_routes(self) -> None:
        """Абстрактный метод для настройки маршрутов. Должен быть реализован в подклассах."""
        raise NotImplementedError()

    @property
    def router(self) -> APIRouter:
        """Возвращает роутер."""
        self.setup_routes()
        return self._router

    @staticmethod
    def good_response(
        message: str = "Успешно",
        data: dict[str, Any] | None = None,
    ) -> GoodResponse:
        """
        Успешный результат

        :param message: Сообщение, defaults to "Успешно"
        :param data: Полезная нагрузка, defaults to None
        :return: GoodResponse
        """
        return GoodResponse(
            message=message,
            data=data,
        )

    @staticmethod
    def bad_response(
        message: str = "Что то пошло не так",
        data: dict[str, Any] | None = None,
    ) -> BadResponse:
        """
        Результат с ошибкой

        :param message: Сообщение, defaults to "Что то пошло не так"
        :param data: Полезная нагрузка, defaults to None
        :return: BadResponse
        """
        return BadResponse(
            message=message,
            data=data,
        )
