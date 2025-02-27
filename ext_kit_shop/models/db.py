"""
:mod:`db` -- Модели для работы с Базой
===================================
.. moduleauthor:: ilya Barinov <i-barinov@it-serv.ru>
"""

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from ext_kit_shop.utils.jwt_helper import JWTHelper


class Base(DeclarativeBase):
    """Базовый класс для моделей"""

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )


class User(Base):
    """Таблица с пользователями"""

    __tablename__ = "user"

    login: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    first_name: Mapped[str] = mapped_column(String, nullable=True)
    last_name: Mapped[str] = mapped_column(String, nullable=True)

    def create_token(self, session: Session) -> str:
        """
        Создание JWT токена

        :return: токен
        """
        token = JWTHelper.create_token(
            {"user_id": self.id},
        )
        self.jwt_token = token

        session.commit()

        return token

    def verify_token(self) -> dict[str, Any] | None:
        """Верификация токена"""
        return JWTHelper.verify_token(
            token=self.jwt_token,
        )

    # Отдельный метод чтоб не было путаницы
    get_payload = verify_token


class Sale(Base):
    """Модель для хранения данных о продаже"""

    __tablename__ = "sales"

    sale_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    device_id: Mapped[int] = mapped_column(Integer, nullable=False)
    shop_id: Mapped[int] = mapped_column(Integer, nullable=False)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False)
    sum: Mapped[float] = mapped_column(Float, nullable=False)
    sale_date_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    server_date_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    pay_type: Mapped[int] = mapped_column(Integer, nullable=False)
    pay_details: Mapped[str] = mapped_column(String, nullable=True)
    is_fiscal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    customer_id: Mapped[int] = mapped_column(Integer, nullable=True)
