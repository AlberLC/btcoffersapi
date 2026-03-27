import asyncio

import aiohttp
from fastapi import status

from api.schemas.offers import Offer
from config import config
from enums import Exchange


async def fetch_offers(eur_dolar_rate: float, btc_price: float, session: aiohttp.ClientSession) -> list[Offer]:
    offers_data = []

    params = {
        'pagination[limit]': config.hodlhodl_pagination_size,
        'filters[side]': 'sell',
        'filters[currency_code]': 'EUR'
    }
    pagination_offset = 0

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
            if offer_data['searchable']:
                offers_data.append(offer_data)

        pagination_offset += config.hodlhodl_pagination_size

        await asyncio.sleep(config.hodlhodl_pagination_sleep)

    offers = []

    for offer_data in offers_data:
        offer_payment_method_ids = {
            payment_method_data['payment_method_id']
            for payment_method_data in offer_data['payment_method_instructions']
        }
        payment_methods = []

        for payment_method, payment_method_ids in config.hodlhodl_payment_methods_ids.items():
            if payment_method_ids & offer_payment_method_ids:
                payment_methods.append(payment_method)

        if not payment_methods:
            continue

        offer_id = offer_data['id']

        if offer_data['min_amount'] == offer_data['max_amount']:
            amount_value = offer_data['min_amount']
        else:
            amount_value = f'{offer_data['min_amount']} - {offer_data['max_amount']}'

        offers.append(
            Offer(
                exchange=Exchange.HODLHODL,
                id=offer_id,
                amount=f'{amount_value} €',
                price_eur=float(offer_data['price']),
                price_usd=float(offer_data['price']) * eur_dolar_rate,
                premium=(float(offer_data['price']) - btc_price) / btc_price * 100,
                payment_methods=payment_methods,
                author=offer_data['trader']['login'],
                trades=offer_data['trader']['trades_count'],
                rating=offer_data['trader']['rating'],
                url=f'{config.hodlhodl_offers_web_base_url}/{offer_id}',
                description=offer_data['description']
            )
        )

    return offers
