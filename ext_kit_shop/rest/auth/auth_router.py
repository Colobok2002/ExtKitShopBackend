"""
:mod:`AuthRouter` -- Роутер для авторизации
===================================
.. moduleauthor:: ilya Barinov <i-barinov@it-serv.ru>
"""

from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel

from ext_kit_shop.models.db import User
from ext_kit_shop.models.request import BadResponse, GoodResponse
from ext_kit_shop.rest.common import RoutsCommon

__all__ = ("AuthRouter",)


class UserCreateRequest(BaseModel):
    login: str
    password: str
    first_name: str
    last_name: str
    api_access_id: int


class ApiAccessCreateRequest(BaseModel):
    company_id: int
    user_login: str
    password: str


class AuthRouter(RoutsCommon):
    """Роутер для авторизации"""

    def setup_routes(self) -> None:
        """Функция назначения routs"""
        self._router.add_api_route("/login", self.login, methods=["GET"])
        self._router.add_api_route("/regist", self.regist, methods=["POST"])
        self._router.add_api_route("/test-ks-manager", self.test_ks_manager, methods=["GET"])

    async def regist(self, request: UserCreateRequest) -> GoodResponse:
        with self.db_helper.sessionmanager() as session:
            user = User(
                login=request.login,
                password=request.password,
                first_name=request.first_name,
                last_name=request.last_name,
                api_access_id=request.api_access_id,
            )
            session.add(user)
            session.commit()
        return GoodResponse(message="User created successfully")

    # Роут для авторизации пользователя
    async def login(
        self,
        username: str,
        password: str,
    ) -> GoodResponse | BadResponse:
        with self.db_helper.sessionmanager() as session:
            user = (
                session.query(User)
                .filter(User.login == username, User.password == password)
                .first()
            )
            if not user:
                return BadResponse(message="Invalid credentials")

            token = user.create_token(session)
        return GoodResponse(message=f"Login successful. Token: {token}")

    async def test_ks_manager(self) -> Any:
        to_date = datetime.now()
        up_date = to_date - timedelta(days=1)

        # Форматируем даты
        up_date_str = up_date.strftime("%d.%m.%Y 00:00:00")
        to_date_str = to_date.strftime("%d.%m.%Y 23:59:59")

        # return self.kit_shop_manger._get_sales_ks(up_date_str, to_date_str)
        # return self.kit_shop_manger._get_sales_about_ks(18390354)
        # return self.kit_shop_manger.get_sales_by_period(up_date_str, to_date_str)
        return self.kit_shop_manger.get_users_info()
