from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict

from api.schemas.enums import Exchange, PaymentMethod


class Offer(BaseModel):
    id: Annotated[str, BeforeValidator(str)]
    exchange: Exchange
    author: str | None = None
    amount: str
    price_eur: float
    price_usd: float
    premium: float
    payment_methods: list[PaymentMethod]
    description: str | None = None

    model_config = ConfigDict(use_enum_values=True)
