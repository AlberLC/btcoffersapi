from collections.abc import Sequence

from api.schemas.dated_offers import DatedOffer, DatedOffers
from database.client import database
from database.locks import database_lock
from database.repositories.offer_repository import OfferRepository
from enums import Exchange, PaymentMethod


async def get_dated_offer(id: str, offer_repository: OfferRepository) -> DatedOffer:
    async with database_lock():
        metadata = await database['metadata'].find_one({'_id': 'offer'})

        return DatedOffer(
            offer=await offer_repository.get_by_id(id),
            updated_at=metadata.get('updated_at') if metadata else None
        )


async def get_dated_offers(
    offer_repository: OfferRepository,
    max_price_eur: float | None = None,
    max_price_usd: float | None = None,
    max_premium: float | None = None,
    payment_methods: Sequence[PaymentMethod] = (),
    exchanges: Sequence[Exchange] = (),
    ignore_ids: Sequence[str] = (),
    ignore_authors: Sequence[str] = (),
    ignore_descriptions: Sequence[str] = (),
    limit: int | None = None
) -> DatedOffers:
    async with database_lock():
        metadata = await database['metadata'].find_one({'_id': 'offer'})

        return DatedOffers(
            offers=await offer_repository.get_offers(
                max_price_eur,
                max_price_usd,
                max_premium,
                payment_methods,
                exchanges,
                ignore_ids,
                ignore_authors,
                ignore_descriptions,
                limit,
                should_lock=False
            ),
            updated_at=metadata.get('updated_at') if metadata else None
        )
