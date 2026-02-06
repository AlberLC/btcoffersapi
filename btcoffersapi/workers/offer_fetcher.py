import asyncio
import datetime
import itertools

import aiohttp

from config import config
from database.client import database
from database.locks import database_lock
from database.repositories.offer_repository import OfferRepository
from services import hodlhodl, lnp2pbot, robosats


async def fetch_offers() -> None:
    offer_repository = OfferRepository()

    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(config.yadio_api_endpoint) as response:
                    yadio_data = await response.json()

                offers = itertools.chain.from_iterable(
                    await asyncio.gather(
                        hodlhodl.fetch_offers(session, yadio_data['EUR']['USD'], yadio_data['BTC']),
                        lnp2pbot.fetch_offers_from_web(yadio_data['EUR']['USD'], yadio_data['BTC']),
                        robosats.fetch_offers(session, yadio_data['EUR']['USD'])
                    )
                )

                async with database_lock():
                    await offer_repository.delete_many({})
                    await offer_repository.insert_many(offers)
                    await database['metadata'].update_one(
                        {'_id': 'offer'},
                        {'$set': {'updated_at': datetime.datetime.now(datetime.UTC)}},
                        upsert=True
                    )
        except (aiohttp.ClientConnectorError, aiohttp.ConnectionTimeoutError):
            pass

        await asyncio.sleep(config.offers_fetch_sleep)


def run() -> None:
    asyncio.run(fetch_offers())
