from pydantic import BaseModel, ConfigDict

from api.schemas.enums import Exchange, PaymentMethod


class Offer(BaseModel):
    id: str
    exchange: Exchange
    author: str | None = None
    amount: str
    price_eur: float
    price_usd: float
    premium: float
    payment_methods: list[PaymentMethod]
    description: str | None = None

    model_config = ConfigDict(use_enum_values=True)
