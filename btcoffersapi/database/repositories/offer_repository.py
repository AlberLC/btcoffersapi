import re
from collections.abc import Sequence

from api.schemas.offers import Offer
from database.client import database
from database.locks import database_lock
from database.repositories.repository import Repository
from enums import Exchange, PaymentMethod


class OfferRepository(Repository[Offer]):
    def __init__(self) -> None:
        super().__init__(database['offer'])

    async def get_offers(
        self,
        max_price_eur: float | None = None,
        max_price_usd: float | None = None,
        max_premium: float | None = None,
        payment_methods: Sequence[PaymentMethod] = (),
        exchanges: Sequence[Exchange] = (),
        ignore_ids: Sequence[str] = (),
        ignore_authors: Sequence[str] = (),
        ignore_descriptions: Sequence[str] = (),
        limit: int | None = None,
        should_lock: bool = True
    ) -> list[Offer]:
        filter = {}

        if max_price_eur is not None:
            filter['price_eur'] = {"$lte": max_price_eur}

        if max_price_usd is not None:
            filter['price_usd'] = {"$lte": max_price_usd}

        if max_premium is not None:
            filter['premium'] = {"$lte": max_premium}

        if payment_methods:
            filter['payment_methods'] = {'$in': [payment_method.value for payment_method in payment_methods]}

        if exchanges:
            filter['exchange'] = {'$in': [exchange.value for exchange in exchanges]}

        if ignore_ids:
            filter['id'] = {'$nin': ignore_ids}

        if ignore_authors:
            filter['author'] = {'$nin': ignore_authors}

        if ignore_descriptions:
            filter['description'] = {
                '$not': {'$regex': '|'.join(re.escape(description) for description in ignore_descriptions)}
            }

        async with database_lock(should_lock):
            return await self.get(filter, sort_keys=('price_eur',), limit=limit)
