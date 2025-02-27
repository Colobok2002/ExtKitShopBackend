"""
:mod:`AuthRouter` -- Роутер для авторизации
===================================
.. moduleauthor:: ilya Barinov <i-barinov@it-serv.ru>
"""

from ext_kit_shop.models.request import GoodResponse
from ext_kit_shop.rest.common import RoutsCommon

__all__ = ("AuthRouter",)


class AuthRouter(RoutsCommon):
    """Роутер для авторизации"""

    def setup_routes(self) -> None:
        """Функция назначения routs"""
        self._router.add_api_route("/login", self.login, methods=["POST"])
        self._router.add_api_route("/regist", self.regist, methods=["POST"])

    def login(self, username: str, password: str) -> GoodResponse:
        return GoodResponse()

    def regist(self, username: str, password: str) -> GoodResponse:
        return GoodResponse()
