"""
:mod:`logger` -- logger
===================================
.. moduleauthor:: ilya Barinov <i-barinov@it-serv.ru>
"""

import re
from collections.abc import Mapping
from logging import (
    ERROR,
    Formatter,
    Logger,
    LogRecord,
    StreamHandler,
    getLogger,
    setLoggerClass,
    setLogRecordFactory,
)
from sys import stderr, stdout
from textwrap import indent
from types import TracebackType
from typing import Any, Protocol, TypeVar

import yaml
import yaml.emitter
import yaml.representer
import yaml.resolver
import yaml.serializer

__all__ = (
    "PrettyDumper",
    "StderrHandler",
    "StdoutHandler",
    "get_logger",
)


# Т.к. yaml аннотирована с помощью stubs, мы не можем использовать типизацию оттуда.
# Поэтому просто копируем нужные определения
_T_contra = TypeVar("_T_contra", str, bytes, contravariant=True)


class _WriteStream(Protocol[_T_contra]):
    def write(self, data: _T_contra, /) -> object: ...

    # Optional fields:
    # encoding: str
    # def flush(self) -> object: ...


class IndentingEmitter(yaml.emitter.Emitter):
    """https://stackoverflow.com/a/70423579"""

    def increase_indent(self, flow: bool = False, indentless: bool = False) -> None:
        """Ensure that lists items are always indented."""
        return super().increase_indent(
            flow=False,
            indentless=False,
        )


class PrettyDumper(
    IndentingEmitter,
    yaml.serializer.Serializer,
    yaml.representer.Representer,
    yaml.resolver.Resolver,
):
    """https://stackoverflow.com/a/70423579"""

    def __init__(
        self,
        stream: _WriteStream[Any],
        default_style: str | None = None,
        default_flow_style: bool = False,
        canonical: bool | None = None,
        indent: int | None = None,
        width: int | None = None,
        allow_unicode: bool | None = None,
        line_break: str | None = None,
        encoding: Any | None = None,
        explicit_start: Any | None = None,
        explicit_end: Any | None = None,
        version: Any | None = None,
        tags: Any | None = None,
        sort_keys: bool = True,
    ):
        IndentingEmitter.__init__(
            self,
            stream,
            canonical=canonical,
            indent=indent,
            width=width,
            allow_unicode=allow_unicode,
            line_break=line_break,
        )
        yaml.serializer.Serializer.__init__(
            self,
            encoding=encoding,
            explicit_start=explicit_start,
            explicit_end=explicit_end,
            version=version,
            tags=tags,
        )
        yaml.representer.Representer.__init__(
            self,
            default_style=default_style,
            default_flow_style=default_flow_style,
            sort_keys=sort_keys,
        )
        yaml.resolver.Resolver.__init__(self)


# Наименование атрибута для хранения extra параметрами
_EXTRA_ARGS_NAME = "_extra_args"
# Т.к. logging аннотирована с помощью stubs, мы не можем использовать типизацию оттуда.
# Поэтому просто копируем нужные определения
type _ArgsType = tuple[object, ...] | Mapping[str, object]
type _SysExcInfoType = (
    tuple[type[BaseException], BaseException, TracebackType | None] | tuple[None, None, None]
)


class LoggerExt(Logger):
    """Расширенный class:`Logger`"""

    def makeRecord(
        self,
        name: str,
        level: int,
        fn: str,
        lno: int,
        msg: object,
        args: _ArgsType,
        exc_info: _SysExcInfoType | None,
        func: str | None = None,
        extra: Mapping[str, object] | None = None,
        sinfo: str | None = None,
    ) -> LogRecord:
        """
        Расширение базового метода: добавление атрибута `_EXTRA_ARGS_NAME`
        для хранения extra параметров
        """
        rv = super().makeRecord(
            name=name,
            level=level,
            fn=fn,
            lno=lno,
            msg=msg,
            args=args,
            exc_info=exc_info,
            func=func,
            extra=extra,
            sinfo=sinfo,
        )

        # Добавляем дополнительный атрибут
        if extra is not None:
            if _EXTRA_ARGS_NAME in rv.__dict__:
                raise KeyError(f"Attempt to overwrite {_EXTRA_ARGS_NAME} in LogRecord")

            rv.__dict__[_EXTRA_ARGS_NAME] = extra

        return rv


class LogRecordExt(LogRecord):
    """Расширенный class:`LogRecord`"""

    def getMessage(self) -> str:
        """
        Расширение базового метода: добавление в сообщение extra параметров
        (если они были переданы)
        """
        msg = super().getMessage()

        extra = getattr(self, _EXTRA_ARGS_NAME, None)

        if extra:
            if msg[-1:] != "\n":
                msg += "\n"
            msg += "Extra args (YAML):\n"
            # msg += indent(yaml.dump(extra, Dumper=PrettyDumper), ' ├──> ')
            msg += indent(yaml.dump(extra, Dumper=PrettyDumper), " └──> ")[:-1]

        return msg


def get_logger(name: str, extra: bool = True) -> Logger:
    """
    :param name: Имя логгера
    :param extra: Добавить обработчик extra параметров (в этом случае extra параметры выгружаются в
        лог)
    """
    if extra:
        setLoggerClass(LoggerExt)
        setLogRecordFactory(LogRecordExt)

    logger_ = getLogger(name)
    logger_.propagate = False

    return logger_


class SensitiveFormatter(Formatter):
    """Formatter that removes sensitive information in urls."""

    @staticmethod
    def _filter(s: str) -> str:
        return re.sub(r":\/\/(.*?)\@", r"://", s)

    def format(self, record: LogRecord) -> Any:
        original = super().format(record)
        return self._filter(original)


DefaultFormatter = SensitiveFormatter(
    "%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) "
    "- %(message)s"
)


class StdoutHandler(StreamHandler[Any]):
    """
    Вывод записей журнала с уровнем < ERROR в stdout
    Установка в качестве форматтера по-умолчанию class:``
    """

    def __init__(self, stream: Any = None) -> None:
        """
        Переопределение конструктора: потока вывода по-умолчанию - stdout,
        установка фильтра записей
        """
        super().__init__(stream or stdout)
        self.addFilter(self.error_record_filter)
        self.setFormatter(DefaultFormatter)

    @staticmethod
    def error_record_filter(record: LogRecord) -> bool:
        """Отправляем в stdout записи с уровнем логирование меньшим чем ERROR"""
        return record.levelno < ERROR


class StderrHandler(StreamHandler[Any]):
    """Вывод записей журнала с уровнем >= ERROR в stderr"""

    def __init__(self, stream: Any = None) -> None:
        """Переопределение конструктора: установка фильтра записей"""
        super().__init__(stream or stderr)
        self.setLevel(ERROR)
        self.setFormatter(DefaultFormatter)
