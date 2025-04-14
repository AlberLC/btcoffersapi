import asyncio

import aiohttp

from config import config
from database.repositories.offer_repository import OfferRepository
from services import hodlhodl, lnp2pbot, robosats


async def fetch_offers(database_lock: asyncio.Lock) -> None:
    offer_repository = OfferRepository()

    while True:

        async with aiohttp.ClientSession() as session:
            async with session.get(config.yadio_api_endpoint) as response:
                yadio_data = await response.json()

            offers = (
                *await hodlhodl.fetch_offers(session, yadio_data['EUR']['USD'], yadio_data['BTC']),
                *await lnp2pbot.fetch_offers(yadio_data['EUR']['USD'], yadio_data['BTC']),
                *await robosats.fetch_offers(session, yadio_data['EUR']['USD']),
            )
            async with database_lock:
                await offer_repository.delete_many({})
                await offer_repository.insert_many(offers)

        await asyncio.sleep(config.fetch_offers_every.total_seconds())
