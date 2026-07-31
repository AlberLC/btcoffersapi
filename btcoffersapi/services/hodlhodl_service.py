import asyncio

import aiohttp
from fastapi import status

from api.schemas.offers import HodlHodlOffer
from config import config
from services.yadio_cache_service import YadioCache


async def fetch_offers(yadio_cache: YadioCache, session: aiohttp.ClientSession) -> set[HodlHodlOffer]:
    params = {
        'pagination[limit]': config.hodlhodl_pagination_size,
        'filters[side]': 'sell',
        'filters[currency_code]': 'EUR'
    }
    pagination_offset = 0
    seen_offer_ids = set()
    offers = set()

    while True:
        params['pagination[offset]'] = pagination_offset
        async with session.get(config.hodlhodl_offers_api_endpoint, params=params) as response:
            if (
                response.status != status.HTTP_200_OK
                or
                not (offers_data_part := (await response.json())['offers'])
            ):
                break

        for offer_data in offers_data_part:
            if offer_data['searchable'] and offer_data['id'] not in seen_offer_ids:
                seen_offer_ids.add(offer_data['id'])

                if offer := HodlHodlOffer.from_data(offer_data, yadio_cache):
                    offers.add(offer)

        pagination_offset += config.hodlhodl_pagination_size

        await asyncio.sleep(config.hodlhodl_pagination_sleep)

    return offers
