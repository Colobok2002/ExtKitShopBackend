"""
:mod:`AuthRouter` -- Роутер для авторизации
===================================
.. moduleauthor:: ilya Barinov <i-barinov@it-serv.ru>
"""

from pydantic import BaseModel

from ext_kit_shop.models.db import ApiAccess, User
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
        self._router.add_api_route("/create_api_access", self.create_api_access, methods=["POST"])

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

    async def create_api_access(
        self,
        request: ApiAccessCreateRequest,
    ) -> GoodResponse:
        with self.db_helper.sessionmanager() as session:
            api_access = ApiAccess(
                company_id=request.company_id,
                user_login=request.user_login,
                password=request.password,
            )
            session.add(api_access)
            session.commit()
            api_access_id = api_access.id
        return GoodResponse(
            message="API access created successfully", data={"api_access": api_access_id}
        )

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
