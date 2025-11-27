from typing import Any, Self

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, model_validator

from api.schemas.enums import Exchange, PaymentMethod


class OffersParams(BaseModel):
    max_price_eur: float | None = None
    max_price_usd: float | None = None
    max_premium: float | None = None
    payment_methods: list[PaymentMethod] = []
    exchanges: list[Exchange] = []
    ignore_authors: list[str] = []
    limit: int | None = None

    model_config = ConfigDict(extra='forbid', use_enum_values=True)

    # noinspection PyNestedDecorators
    @model_validator(mode='before')
    @classmethod
    def validate_before(cls, data: Any) -> Any:
        data['payment_methods'] = [
            payment_method
            for payment_methods in data['payment_methods']
            for payment_method in payment_methods.split(',')
            if payment_method
        ]
        data['exchanges'] = [
            exchange
            for exchanges in data['exchanges']
            for exchange in exchanges.split(',')
            if exchange
        ]
        data['ignore_authors'] = [
            ignore_author
            for ignore_authors in data['ignore_authors']
            for ignore_author in ignore_authors.split(',')
            if ignore_author
        ]

        return data

    @model_validator(mode='after')
    def validate_after(self) -> Self:
        if len(
            [
                parameter for parameter in (self.max_price_eur, self.max_price_usd, self.max_premium)
                if parameter is not None
            ]
        ) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You must provide only one of the following parameters: 'max_price_eur', 'max_price_usd', or 'max_premium'."
            )

        self.payment_methods = [PaymentMethod(payment_method) for payment_method in self.payment_methods]
        self.exchanges = [Exchange(exchange) for exchange in self.exchanges]

        return self
