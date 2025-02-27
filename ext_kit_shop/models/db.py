"""
:mod:`db` -- Модели для работы с Базой
===================================
.. moduleauthor:: ilya Barinov <i-barinov@it-serv.ru>
"""

import datetime
from enum import Enum
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

from ext_kit_shop.utils.jwt_helper import JWTHelper


class Base(DeclarativeBase):
    """Базовый класс для моделей"""

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
