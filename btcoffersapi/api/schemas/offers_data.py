import datetime

from pydantic import BaseModel

from api.schemas.offer import Offer


class OfferData(BaseModel):
    offer: Offer | None
    updated_at: datetime.datetime | None

    def __bool__(self) -> bool:
        return bool(self.offer)


class OffersData(BaseModel):
    offers: list[Offer]
    updated_at: datetime.datetime | None

    def __bool__(self) -> bool:
        return bool(self.offers)
