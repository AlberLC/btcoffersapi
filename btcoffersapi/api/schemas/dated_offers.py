import datetime

from pydantic import BaseModel

from api.schemas.offers import Offer


class DatedOffer(BaseModel):
    offer: Offer | None
    updated_at: datetime.datetime | None

    def __bool__(self) -> bool:
        return bool(self.offer)


class DatedOffers(BaseModel):
    offers: list[Offer]
    updated_at: datetime.datetime | None

    def __bool__(self) -> bool:
        return bool(self.offers)
