import asyncio

import aiohttp

from btcoffersapi.config import config
from btcoffersapi.database.locks import database_lock
from btcoffersapi.database.repositories.offer_repository import OfferRepository
from btcoffersapi.services import hodlhodl, lnp2pbot, robosats


async def fetch_offers() -> None:
    offer_repository = OfferRepository()

    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(config.yadio_api_endpoint) as response:
                    yadio_data = await response.json()

            offers = (
                *await hodlhodl.fetch_offers(session, yadio_data['EUR']['USD'], yadio_data['BTC']),
                *await lnp2pbot.fetch_offers(yadio_data['EUR']['USD'], yadio_data['BTC']),
                *await robosats.fetch_offers(session, yadio_data['EUR']['USD']),
            )
            async with database_lock():
                await offer_repository.delete_many({})
                await offer_repository.insert_many(offers)
                offers = (
                    *await hodlhodl.fetch_offers(session, yadio_data['EUR']['USD'], yadio_data['BTC']),
                    *await robosats.fetch_offers(session, yadio_data['EUR']['USD']),
                )
                async with database_lock():
                    await offer_repository.delete_many({})
                    await offer_repository.insert_many(offers)
        except aiohttp.ClientConnectorError:
            pass

        await asyncio.sleep(config.fetch_offers_every.total_seconds())


asyncio.run(fetch_offers())
