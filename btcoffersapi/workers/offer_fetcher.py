import asyncio
import datetime
import itertools
from typing import Never

import aiohttp

from config import config
from database.client import database
from database.locks import database_lock
from database.repositories.offer_repository import OfferRepository
from services import hodlhodl_service, robosats_service, yadio_service
from services.lnp2pbot import lnp2pbot_nostr_service


async def run_offer_fetcher() -> Never:
    offer_repository = OfferRepository()

    asyncio.create_task(lnp2pbot_nostr_service.run_nostr_offer_fetcher(offer_repository))

    robosats_url = await robosats_service.fetch_robosats_url()

    while True:
        async with aiohttp.ClientSession() as session:
            try:
                yadio_data = await yadio_service.fetch_yadio_data(session)

                lnp2pbot_cleanup_task = asyncio.create_task(
                    lnp2pbot_nostr_service.clean_up_invalid_offers(offer_repository, session)
                )

                offers = itertools.chain.from_iterable(
                    await asyncio.gather(
                        hodlhodl_service.fetch_offers(yadio_data['EUR']['USD'], yadio_data['BTC'], session),
                        robosats_service.fetch_offers(robosats_url, yadio_data['EUR']['USD'], session)
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
