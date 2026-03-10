from pydantic import BaseModel, ConfigDict

from enums import Exchange, PaymentMethod


class Offer(BaseModel):
    id: str
    exchange: Exchange
    amount: str
    price_eur: float
    price_usd: float
    premium: float
    payment_methods: list[PaymentMethod]
    description: str | None = None
    author: str | None = None
    trades: int | None = None
    rating: float | None = None
    url: str | None = None

    model_config = ConfigDict(use_enum_values=True)
