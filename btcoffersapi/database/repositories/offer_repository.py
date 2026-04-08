import asyncio
import datetime
import re
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import Any

from api.schemas.offers import Offer
from config import config
from database.client import database
from database.repositories.repository import Repository
from enums import Exchange, PaymentMethod


class OfferRepository(Repository[Offer]):
    def __init__(self) -> None:
        super().__init__(database['offer'])
        self._lock = asyncio.Lock()
        self._locks_collection = database['locks']

    @staticmethod
    def _build_filter(
        max_price_eur: float | None = None,
        max_price_usd: float | None = None,
        max_premium: float | None = None,
        payment_methods: Sequence[PaymentMethod] = (),
        exchanges: Sequence[Exchange] = (),
        ignore_ids: Sequence[str] = (),
        ignore_authors: Sequence[str] = (),
        ignore_descriptions: Sequence[str] = ()
    ) -> dict[str, Any]:
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

        return filter

    async def delete_offers(
        self,
        max_price_eur: float | None = None,
        max_price_usd: float | None = None,
        max_premium: float | None = None,
        payment_methods: Sequence[PaymentMethod] = (),
        exchanges: Sequence[Exchange] = (),
        ignore_ids: Sequence[str] = (),
        ignore_authors: Sequence[str] = (),
        ignore_descriptions: Sequence[str] = ()
    ):
        filter = self._build_filter(
            max_price_eur,
            max_price_usd,
            max_premium,
            payment_methods,
            exchanges,
            ignore_ids,
            ignore_authors,
            ignore_descriptions
        )

        await self.delete(filter)

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
        limit: int | None = None
    ) -> list[Offer]:
        filter = self._build_filter(
            max_price_eur,
            max_price_usd,
            max_premium,
            payment_methods,
            exchanges,
            ignore_ids,
            ignore_authors,
            ignore_descriptions
        )

        return await self.get(filter, sort_keys=('price_eur',), limit=limit)

    @asynccontextmanager
    async def lock(self) -> AsyncIterator[None]:
        async with self._lock:
            while await self._locks_collection.find_one(
                {'_id': 'offers_lock', 'until': {'$gte': datetime.datetime.now(datetime.UTC)}}
            ):
                await asyncio.sleep(1)

            await self._locks_collection.update_one(
                {'_id': 'offers_lock'},
                {
                    '$set': {
                        'until': datetime.datetime.now(datetime.UTC) + config.database_lock_expiration
                    }
                },
                upsert=True
            )

            try:
                yield
            finally:
                await self._locks_collection.delete_one({'_id': 'offers_lock'})
