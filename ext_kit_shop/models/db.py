"""
:mod:`db` -- Модели для работы с Базой
===================================
.. moduleauthor:: ilya Barinov <i-barinov@it-serv.ru>
"""

from typing import Any

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

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

    # TODO: Вынести в компанию
    # user_type: Mapped[str] = mapped_column(String, nullable=True)  # Тип пользователя
    # company_name: Mapped[str] = mapped_column(String, nullable=True)  # Название компании
    # inn: Mapped[str] = mapped_column(String, nullable=True)  # ИНН компании

    api_access_id: Mapped[int] = mapped_column(ForeignKey("api_access.id"), nullable=True)
    api_access: Mapped["ApiAccess"] = relationship(
        "ApiAccess", back_populates="user", uselist=False
    )

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


class ApiAccess(Base):
    """Таблица с API доступами"""

    __tablename__ = "api_access"

    company_id: Mapped[int] = mapped_column(String, nullable=False)
    user_login: Mapped[str] = mapped_column(String, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="api_access")
