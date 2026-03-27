import aiohttp

from api.schemas.offers import Offer
from config import config
from enums import Exchange
from services import payment_method_service


async def fetch_offers_from_api(eur_dolar_rate: float, btc_price: float, session: aiohttp.ClientSession) -> list[Offer]:
    async with session.get(config.lnp2pbot_api_endpoint) as response:
        offers_data = (await response.json())

    offers = []
    for offer_data in offers_data:
        if (
            offer_data['type'] != 'sell'
            or
            offer_data['fiat_code'].lower() != 'eur'
            or
            not (payment_methods := payment_method_service.find_payment_methods(offer_data['payment_method']))
        ):
            continue

        if offer_data['fiat_amount']:
            amount_value = f'{float(offer_data['fiat_amount']):.2f}'
        else:
            amount_value = f'{float(offer_data['min_amount']):.2f} - {float(offer_data['max_amount']):.2f}'

        premium = float(offer_data['price_margin'])
        price_eur = btc_price + premium / 100 * btc_price

        offers.append(
            Offer(
                exchange=Exchange.LNP2PBOT,
                id=offer_data['_id'],
                amount=f'{amount_value} €',
                price_eur=price_eur,
                price_usd=price_eur * eur_dolar_rate,
                premium=float(offer_data['price_margin']),
                payment_methods=payment_methods,
                description=offer_data['description']
            )
        )

    return offers
