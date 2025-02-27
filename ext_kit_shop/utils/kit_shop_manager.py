"""
:mod:`kit_shop_manager` -- docs
===================================
.. moduleauthor:: ilya Barinov <i-barinov@it-serv.ru>
"""

import hashlib
import json
from datetime import datetime
from logging import Logger, getLogger

import requests
from pydantic import BaseModel

from ext_kit_shop.models.kit_shop import (
    CustomerModel,
    PositionModel,
    SaleModel,
    SalesAboutModel,
)
from ext_kit_shop.utils.db_helper import DBHelper

# region CONSTS
URL_GET_SALES = "https://api.kitshop.ru/APIService.svc/GetSales"
URL_GET_SALE_ABOUT = "https://api.kitshop.ru/APIService.svc/GetSaleById"
URL_GET_CUSTOMERS = "https://api.kitshop.ru/APIService.svc/GetCustomers"

# endregion


class ApiAccess(BaseModel):
    """Модель с доступами к API"""

    __tablename__ = "api_access"

    company_id: int
    user_login: str
    password: str

    def generate_sign(self, request_id: str) -> str:
        """Генерация подписи"""
        return hashlib.md5(f"{self.company_id}{self.password}{request_id}".encode()).hexdigest()

    def get_auth_headers(self) -> dict[str, int | str]:
        """Заголовки авторизации"""
        request_id = datetime.now().strftime("%d%m%Y%H%M%S")
        return {
            "CompanyId": self.company_id,
            "RequestId": request_id,
            "UserLogin": self.user_login,
            "Sign": self.generate_sign(request_id),
        }


class KitShopManager:
    def __init__(
        self,
        db_helper: DBHelper,
        api_access: ApiAccess,
        logger: Logger | None = None,
    ):
        self.db_helper = db_helper
        self.logger = logger if logger else getLogger()
        self.api_access = api_access

    def _get_sales_ks(self, up_date: str, to_date: str) -> list[SaleModel] | None:
        """
        Получение продаж за указанный период.

        :param up_date: Начальная дата (в формате "дд.мм.гггг чч:мм:сс")
        :param to_date: Конечная дата (в формате "дд.мм.гггг чч:мм:сс")
        :return: Список продаж или None при ошибке
        """
        sales_data = {
            "Auth": self.api_access.get_auth_headers(),
            "Filter": {"UpDate": up_date, "ToDate": to_date},
        }
        response = requests.post(URL_GET_SALES, data=json.dumps(sales_data))

        if (
            response.status_code != requests.codes.ok
            or response.json().get("ResultCode", None) != 0
        ):
            self.logger.error(
                f"Ошибка при запросе {URL_GET_SALES}: {response.status_code}",
                extra={
                    "method": URL_GET_SALES,
                    "status_code": response.status_code,
                },
            )
            return None

        try:
            sales = response.json().get("Sales")
            self.logger.error(f"Список продаж с {up_date} по {to_date} успешно загружен")
            return [SaleModel(**sale) for sale in sales]
        except Exception as e:
            self.logger.error(f"Ошибка обработки данных о продажах: {e}")
            return None

    def _get_sales_about_ks(self, sale_id: int) -> SalesAboutModel | None:
        """
        Получение продаж за указанный период.

        :param up_date: Начальная дата (в формате "дд.мм.гггг чч:мм:сс")
        :param to_date: Конечная дата (в формате "дд.мм.гггг чч:мм:сс")
        :return: Список продаж или None при ошибке
        """
        sales_about_data = {
            "Auth": self.api_access.get_auth_headers(),
            "Id": sale_id,
        }
        response = requests.post(URL_GET_SALE_ABOUT, data=json.dumps(sales_about_data))

        if (
            response.status_code != requests.codes.ok
            or response.json().get("ResultCode", None) != 0
        ):
            self.logger.error(
                f"Ошибка при запросе {URL_GET_SALES}: {response.status_code}",
                extra={
                    "method": URL_GET_SALES,
                    "status_code": response.status_code,
                },
            )
            return None

        try:
            sale_info = response.json().get("Sales")[0]
            self.logger.info("Подробная информация о продаже получена", extra=sale_info)
            sale_info["Positions"] = [
                PositionModel(**position) for position in sale_info["Positions"]
            ]
            return SalesAboutModel(**sale_info)
        except Exception as e:
            self.logger.error(f"Ошибка обработки данных о продажах: {e}")
            return None

    def get_users_info(self) -> list[CustomerModel] | None:
        get_users = {
            "Auth": self.api_access.get_auth_headers(),
        }
        response = requests.post(URL_GET_CUSTOMERS, data=json.dumps(get_users))
        if (
            response.status_code != requests.codes.ok
            or response.json().get("ResultCode", None) != 0
        ):
            self.logger.error(
                f"Ошибка при запросе {URL_GET_SALES}: {response.status_code}",
                extra={
                    "method": URL_GET_SALES,
                    "status_code": response.status_code,
                },
            )
            return None

        try:
            sales = response.json().get("Customers")
            self.logger.error("Список пользователей успешно загружен")
            return [CustomerModel(**sale) for sale in sales]
        except Exception as e:
            self.logger.error(f"Ошибка обработки данных о продажах: {e}")
            return None

    # def get_sales_by_period(self, up_date: str, to_date: str) -> list[SalesModelFull] | None:
    #     result = []

    #     sales_info = self._get_sales_ks(up_date, to_date)

    #     if not sales_info:
    #         return None

    #     for sale in sales_info[:10]:
    #         sale_about = self._get_sales_about_ks(sale.SaleId)

    #         result.append(SalesModelFull(**sale.model_dump(), about=sale_about))

    #     return result
