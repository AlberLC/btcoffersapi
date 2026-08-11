import asyncio
import datetime
import itertools
from typing import Never

import aiohttp

from config import config
from database.client import database
from database.repositories.offer_repository import OfferRepository
from enums import Exchange
from services import hodlhodl_service, robosats_service
from services.yadio_cache_service import YadioCache


async def run_offer_fetcher() -> Never:
    offer_repository = OfferRepository()

    async with aiohttp.ClientSession() as session:
        yadio_cache = YadioCache(session)
        await yadio_cache.refresh()

        robosats_url = await robosats_service.fetch_robosats_url(session)

        while True:
            try:
                await yadio_cache.refresh()

                hodlhodl_offers, robosats_offers = await asyncio.gather(
                    hodlhodl_service.fetch_offers(yadio_cache, session),
                    robosats_service.fetch_offers(robosats_url, yadio_cache, session)
                )

                async with offer_repository.lock():
                    await offer_repository.delete_offers(exchanges=(Exchange.HODLHODL, Exchange.ROBOSATS))
                    # noinspection bad-argument-type
                    await offer_repository.insert(itertools.chain(hodlhodl_offers, robosats_offers))
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
