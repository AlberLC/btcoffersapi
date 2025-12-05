from api.schemas.enums import Exchange, PaymentMethod
from api.schemas.offer import Offer
from api.schemas.offers_data import OfferData, OffersData
from database.client import database
from database.locks import database_lock
from database.repositories.repository import Repository


class OfferRepository(Repository[Offer]):
    def __init__(self) -> None:
        super().__init__(database['offer'])

    async def get(
        self,
        max_price_eur: float | None = None,
        max_price_usd: float | None = None,
        max_premium: float | None = None,
        payment_methods: list[PaymentMethod] | None = None,
        exchanges: list[Exchange] | None = None,
        ignore_authors: list[str] | None = None,
        limit: int | None = None,
        should_lock: bool = True
    ) -> OffersData:
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

        if ignore_authors:
            filter['author'] = {'$nin': ignore_authors}

        async with database_lock(should_lock):
            metadata = await database['metadata'].find_one({'_id': 'offer'})

            return OffersData(
                offers=[
                    Offer(**document)
                    async for document in self._collection.find(filter).sort('price_eur').limit(limit if limit else 0)
                ],
                updated_at=metadata.get('updated_at') if metadata else None
            )

    async def get_by_id(self, id: str, should_lock: bool = True) -> OfferData:
        async with database_lock(should_lock):
            document = await self._collection.find_one({'id': id})
            metadata = await database['metadata'].find_one({'_id': 'offer'})

            return OfferData(
                offer=Offer(**document) if document else None,
                updated_at=metadata.get('updated_at') if metadata else None
            )
