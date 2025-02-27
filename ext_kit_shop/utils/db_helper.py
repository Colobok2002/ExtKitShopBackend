"""
:mod:`db_helper` -- Вспомогательные инструменты для работы с SQLAlchemy
===================================
.. moduleauthor:: ilya Barinov <i-barinov@it-serv.ru>
"""

try:
    from collections.abc import Generator
    from contextlib import contextmanager
    from json import dumps, loads
    from logging import NOTSET, basicConfig, getLogger
    from os import getpid
    from typing import Any

    from sqlalchemy import (
        create_engine as sqlalchemy_create_engine,
    )
    from sqlalchemy.dialects import postgresql, sqlite
    from sqlalchemy.engine import Engine
    from sqlalchemy.exc import SQLAlchemyError
    from sqlalchemy.orm.session import Session
    from sqlalchemy.orm.session import sessionmaker as sqlalchemy_sessionmaker
    from sqlalchemy.pool import StaticPool
except ImportError:
    raise ImportError("Install module with SQL: pip install sqlalchemy") from ImportError

__all__ = ("DBHelper",)


def sessionmaker(
    engine: Engine,
    options: dict[str, Any] | None = None,
) -> sqlalchemy_sessionmaker[Any]:
    """
    Создать фабрику для генерации сессий

    :param engine: Экземпляр :class:
    :param options: Дополнительные опции sessionmaker

    :return: Класс :class:`sessionmaker`
    """
    if options is None:
        options = {}

    return sqlalchemy_sessionmaker(
        engine,
        **options,
    )


def create_engine(
    db_url: str,
    application_name: str | None = None,
    engine_options: dict[str, Any] | None = None,
    dialect: str = "postgresql",
    engine_loglevel: str | int = NOTSET,
    pool_recycle: int = 3600,
    **kwargs: Any,
) -> Engine:
    """
    Формирование экземпляра :class:`Engine` для работы с БД

    :param dialect: Диалект
    :param db_url: DB URL
    :param application_name: Наименование приложения
    :param engine_options: Дополнительные опции
    :param engine_loglevel: Уровень логирования
    :param pool_recycle: Срок жизни соединения в пуле, после истечения которого соединение должно
        быть переоткрыто

    :return: Экземпляр :class:`Engine`
    """
    if isinstance(engine_loglevel, str):
        engine_loglevel = engine_loglevel.upper()

    if engine_options is None:
        engine_options = {}

    # https://gehrcke.de/2015/05/in-memory-sqlite-database-and-flask-a-threading-trap/
    if db_url == "sqlite://":
        engine_options["poolclass"] = StaticPool
        engine_options["connect_args"] = {"check_same_thread": False}

    # Для БД, которые не поддерживают JSON устанавливаем кастомные сериализаторы
    if dialect == sqlite.dialect.name:
        # https://docs.sqlalchemy.org/en/13/core/type_basics.html#sqlalchemy.types.JSON
        if not engine_options.get("json_serializer"):
            engine_options["json_serializer"] = (
                lambda obj: dumps(obj, ensure_ascii=False) if obj else None
            )
        if not engine_options.get("json_deserializer"):
            engine_options["json_deserializer"] = loads

    # Формирование объектов для работы с БД
    engine_options["pool_recycle"] = pool_recycle

    # Устанавливаем наименование приложения (только для Postgres)
    if dialect == postgresql.dialect.name and application_name:
        engine_options["connect_args"] = {"application_name": application_name}

    # Настраиваем уровень логирования ядра SQLAlchemy
    if engine_loglevel != NOTSET:
        basicConfig()
        engine_logger = getLogger("sqlalchemy.engine")
        engine_logger.setLevel(engine_loglevel)
        engine_options["echo"] = True

    engine = sqlalchemy_create_engine(db_url, **engine_options, **kwargs)

    return engine


class DBHelperError(Exception):
    """Базовый класс для всех исключений, связанных с `DBHelper`."""

    pass


class EngineNotInitializedError(DBHelperError):
    """
    Исключение, выбрасываемое при попытке выполнения операции,
    если `_engine` не был инициализирован.

    Это может произойти, если база данных не подключена, или
    если метод инициализации `_engine` не был вызван.
    """


class DBHelperBase:
    """Mixin для подключения к БД."""

    def __init__(
        self,
        engine: Engine,
    ) -> None:
        """
        Конструктор экземпляра класса

        Выполняет инициализацию процесса для работы с БД, загрузку метаописания таблиц, подписку на
        события для связи подсистемы аудита и журнала задач

        :param engine: Экземпляр :class:`Engine`
        :param login: Логин пользователя
        :param variables: Переменные сессии
        """
        self._engine: Engine = engine

    @property
    def engine(self) -> Engine | None:
        """Экземпляр :class:`Engine`"""
        return self._engine

    def is_active_engine(self) -> bool:
        """Проверка, что engine не None"""
        return self._engine is not None


class DBHelper(DBHelperBase):
    """Mixin для подключения к БД."""

    def __init__(
        self,
        engine: Engine,
        session_factory: sqlalchemy_sessionmaker[Any] | None = None,
    ) -> None:
        """
        Конструктор экземпляра класса

        Выполняет инициализацию процесса для работы с БД, загрузку метаописания таблиц, подписку на
        события для связи подсистемы аудита и журнала задач

        :param engine: Экземпляр :class:`Engine`
        :param login: Логин пользователя
        :param variables: Переменные сессии
        """
        self._pid: int | None = None

        super().__init__(engine)

        if session_factory is not None:
            self._session_factory = session_factory
        else:
            self._session_factory = sessionmaker(self._engine)

        self._init_db_in_process()

    @contextmanager
    def sessionmanager(
        self,
        session: Session | None = None,
        **kwargs: Any,
    ) -> Generator[Session, Any, Any]:
        """
        Менеджер сессий.

        Инициализирует сессию для работы с БД, выполняет автоматический commit или rollback
        транзакции
        https://docs.sqlalchemy.org/en/13/orm/session_basics.html#when-do-i-construct-a-session-when-do-i-commit-it-and-when-do-i-close-it

        :param session: Сессия SQLAlchemy :class:`Session` (если передана, то новая сессия не
            создается)
        :param login: Логин пользователя
        :param variables: Переменные сессии
        :param expunge_all: Отсоединить объекты от сессии
        :param kwargs: Именованные параметры, передаваемые в конструктор :class:`Session`
        """
        self._init_db_in_process()

        if session is not None:
            yield session
            return

        # TODO: При создании сессии необходимо учитывать временную зону
        session_ = self._session_factory(**kwargs)

        try:
            yield session_
            session_.commit()
        except SQLAlchemyError:
            session_.rollback()
            raise

        finally:
            session_.close()

            self.login = None
            self.variables = None

    def _init_db_in_process(self) -> None:
        """
        Инициализация процесса для работы с БД

        Метод выполняет проверку текущего идентификатора процесса с идентификатором, сохраненным во
        время инициализации класса. Если эти идентификаторы не совпадают, то мы находимся в дочернем
        процессе. В этом случае необходимо выпонить требования `SQLAlchemy <https://docs.sqlalchemy.org/en/20/core/pooling.html#using-connection-pools-with-multiprocessing-or-os-fork>`
        и создать новую сессию.
        """
        if self._pid != getpid():
            self._engine.dispose()
            self._pid = getpid()
