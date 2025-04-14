from typing import Self

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, model_validator

from api.schemas.enums import Exchange, PaymentMethod


class OffersParams(BaseModel):
    max_price_eur: float | None = None
    max_price_usd: float | None = None
    max_premium: float | None = None
    payment_method: list[PaymentMethod] = []
    exchange: list[Exchange] = []

    model_config = ConfigDict(extra='forbid', use_enum_values=True)

    @model_validator(mode='after')
    def validate(self) -> Self:
        if len(
            [parameter for parameter in (self.max_price_eur, self.max_price_usd, self.max_premium) if parameter]
        ) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You must provide only one of the following parameters: 'max_price_eur', 'max_price_usd', or 'max_premium'."
            )

        self.payment_method = [PaymentMethod(payment_method) for payment_method in self.payment_method]
        self.exchange = [Exchange(exchange) for exchange in self.exchange]

        return self
