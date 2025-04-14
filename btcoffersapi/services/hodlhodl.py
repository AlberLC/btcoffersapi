import aiohttp

from api.schemas.enums import Exchange
from api.schemas.offer import Offer
from config import config


async def fetch_offers(session: aiohttp.ClientSession, eur_dolar_rate: float, btc_price: float) -> list[Offer]:
    params = {
        'filters[side]': 'sell',
        'filters[currency_code]': 'EUR'
    }
    async with session.get(config.hodlhodl_offers_endpoint, params=params) as response:
        offers_data = (await response.json())['offers']

    offers = []
    for offer_data in offers_data:
        payment_methods = []
        for payment_method_data in offer_data['payment_method_instructions']:
            try:
                payment_methods.append(config.hodlhodl_payment_methods[payment_method_data['payment_method_id']])
            except KeyError:
                pass

        if not payment_methods:
            continue

        offers.append(
            Offer(
                id=offer_data['id'],
                exchange=Exchange.HODLHODL,
                author=offer_data['trader']['login'],
                amount=f'{offer_data['min_amount'] if offer_data['min_amount'] == offer_data['max_amount'] else f'{offer_data['min_amount']} - {offer_data['max_amount']}'} €',
                price_eur=float(offer_data['price']),
                price_usd=float(offer_data['price']) * eur_dolar_rate,
                premium=(float(offer_data['price']) - btc_price) / btc_price * 100,
                payment_methods=payment_methods,
                description=offer_data['description']
            )
        )

    return offers
