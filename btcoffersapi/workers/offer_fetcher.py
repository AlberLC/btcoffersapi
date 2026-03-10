import asyncio
import datetime
import itertools
from typing import Never

import aiohttp

from config import config
from database.client import database
from database.locks import database_lock
from database.repositories.offer_repository import OfferRepository
from services import hodlhodl, robosats, yadio
from services.lnp2pbot import lnp2pbot_nostr


async def run_offer_fetcher() -> Never:
    offer_repository = OfferRepository()

    asyncio.create_task(lnp2pbot_nostr.run_nostr_offer_fetcher(offer_repository))

    robosats_url = await robosats.fetch_robosats_url()

    while True:
        try:
            async with aiohttp.ClientSession() as session:
                yadio_data = await yadio.fetch_yadio_data(session)

                lnp2pbot_cleanup_task = asyncio.create_task(
                    lnp2pbot_nostr.clean_up_invalid_offers(offer_repository, session)
                )

                offers = itertools.chain.from_iterable(
                    await asyncio.gather(
                        hodlhodl.fetch_offers(session, yadio_data['EUR']['USD'], yadio_data['BTC']),
                        robosats.fetch_offers(session, robosats_url, yadio_data['EUR']['USD'])
                    )
                )

                await lnp2pbot_cleanup_task

                async with database_lock():
                    await offer_repository.delete({'exchange': {'$in': ['HodlHodl', 'RoboSats']}})
                    await offer_repository.insert(offers)
                    await database['metadata'].update_one(
                        {'_id': 'offer'},
                        {'$set': {'updated_at': datetime.datetime.now(datetime.UTC)}},
                        upsert=True
                    )
        except TimeoutError, aiohttp.ClientError:
            pass

        await asyncio.sleep(config.offers_fetch_sleep)


def run() -> Never:
    # noinspection PyUnreachableCode
    asyncio.run(run_offer_fetcher())
