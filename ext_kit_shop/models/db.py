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


class User(Base):
    """Таблица с пользователями"""

    __tablename__ = "user"

    secret_key: Mapped[str] = mapped_column(String)
    jwt_token: Mapped[str] = mapped_column(String)

    logins: Mapped[list["Login"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def create_token(self, session: Session) -> str:
        """
        Создание JWT токена

        :return: токен
        """
        if self.secret_key is None:
            self.secret_key = JWTHelper.generate_secure_jwt_key()

        token = JWTHelper.create_token(
            {"user_id": self.id},
            key=self.secret_key,
        )
        self.jwt_token = token

        session.commit()

        return token

    def verify_token(self) -> dict[str, Any] | None:
        """Верификация токена"""
        return JWTHelper.verify_token(token=self.jwt_token, key=self.secret_key)

    # Отдельный метод чтоб не было путаницы
    get_payload = verify_token


class Login(Base):
    """Таблица с номерами телефонов"""

    __tablename__ = "login"

    login: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )

    token: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
    )

    expires_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    address: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="logins",
        uselist=False,
    )

    devices: Mapped["Devices"] = relationship(
        "Devices",
        back_populates="login",
    )

    def is_expired(self) -> bool:
        """Проверяет, истёк ли токен"""
        if self.expires_at:
            return datetime.datetime.now(datetime.UTC) > self.expires_at
        return True


class Cameras(Base):
    # medium
    __tablename__ = "cameras"

    archive_length: Mapped[int] = mapped_column(
        Integer,
        doc="Количество архивных дней",
        nullable=True,
    )
    rt_id: Mapped[str] = mapped_column(
        String,
        doc="Id в системе rt",
        unique=True,
        nullable=False,
    )
    screenshot_url_template: Mapped[str] = mapped_column(
        String, doc="Шаблон Url для получения снимка"
    )
    screenshot_token: Mapped[str] = mapped_column(
        String,
        doc="Токен для получения скриншота",
    )
    streamer_token: Mapped[str] = mapped_column(
        String,
        doc="Токен для получения видео трансляции",
    )

    login: Mapped[str] = mapped_column(
        String, ForeignKey("login.login", ondelete="CASCADE"), nullable=False
    )

    device: Mapped["Devices"] = relationship(
        "Devices",
        back_populates="camera",
        uselist=False,  # Один к одному
    )


class DeviceType(Enum):
    """Типы устройств"""

    intercom = "intercom"
    barrier = "barrier"


class Devices(Base):
    __tablename__ = "devices"

    rt_id: Mapped[str] = mapped_column(
        String,
        doc="Id в системе rt",
        unique=True,
        nullable=False,
    )
    device_type: Mapped[DeviceType] = mapped_column(
        SQLEnum(DeviceType),
        doc="Тип девайса",
        nullable=False,
    )

    login_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("login.login", ondelete="CASCADE"),
        nullable=False,
    )

    camera_id: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("cameras.rt_id", ondelete="CASCADE"),
        nullable=True,
    )

    description: Mapped[str] = mapped_column(
        String,
    )

    is_favorite: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    name_by_user: Mapped[str] = mapped_column(
        String,
        nullable=True,
    )

    login: Mapped["Cameras"] = relationship(
        Login,
        back_populates="devices",
        uselist=False,
    )

    camera: Mapped["Cameras | None"] = relationship(
        "Cameras",
        back_populates="device",
        uselist=False,  # Один к одному
    )
