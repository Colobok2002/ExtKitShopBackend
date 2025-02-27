from pydantic import BaseModel


class SaleModel(BaseModel):
    """Модель продажи"""

    SaleId: int
    DeviceId: int
    ShopId: int
    CompanyId: int
    Sum: float
    SaleDateTime: str
    ServerDateTime: str
    PayType: int
    PayDetails: str | None = ""
    IsFiscal: bool
    CustomerId: int | None = None


class PositionModel(BaseModel):
    """Модель позиции в продаже"""

    HasDiscount: bool
    HasPromotion: bool
    NominalPrice: float
    PositionId: int
    Price: float
    ProductId: int
    Quantity: float
    SaleId: int


class SalesAboutModel(BaseModel):
    """Модель данных о продаже с вложенными позициями"""

    SaleId: int
    CompanyId: int
    ShopId: int
    DeviceId: int
    SaleDateTime: str
    ServerDateTime: str | None = None
    Sum: float | None = None
    PayType: int | None = None
    IsFiscal: bool | None = None
    PayDetails: str | None = ""
    Positions: list[PositionModel] = []
    CustomerId: int | None = None


class SalesModelFull(SaleModel):
    """Полный отчет о продаже"""

    about: SalesAboutModel | None = None


class CustomerModel(BaseModel):
    """Сотрудник"""

    Balance: float
    CardNumber: str
    CustomerId: int
    CustomerName: str
    LastPurchase: str
    LoyaltyId: int | None = None
    Purchases: int
