import aiohttp
import flanautils
from telethon import TelegramClient
from telethon.sessions import StringSession

from api.schemas.enums import PaymentMethod
from btcoffersapi.api.schemas.enums import Exchange
from btcoffersapi.api.schemas.offer import Offer
from btcoffersapi.config import config

client = TelegramClient(StringSession(config.telegram_user_session), config.telegram_api_id, config.telegram_api_hash)


def _find_payment_methods(text: str) -> list[PaymentMethod]:
    payment_methods = []
    normalized_description = flanautils.remove_accents(text.lower())

    for payment_method_name, payment_method in config.lnp2pbot_payment_methods.items():
        if payment_method_name in normalized_description:
            if payment_method_name == 'instant sepa':
                normalized_description = normalized_description.replace('instant sepa', '')

            if payment_method_name == 'sepa instant':
                normalized_description = normalized_description.replace('sepa instant', '')

            payment_methods.append(payment_method)

    return payment_methods


async def fetch_offers_from_api(session: aiohttp.ClientSession, eur_dolar_rate: float, btc_price: float) -> list[Offer]:
    async with session.get(config.lnp2pbot_api_endpoint) as response:
        offers_data = (await response.json())

    offers = []
    for offer_data in offers_data:
        if (
            offer_data['type'] != 'sell'
            or
            offer_data['fiat_code'].lower() != 'eur'
            or
            not (payment_methods := _find_payment_methods(offer_data['payment_method']))
        ):
            continue

        premium = float(offer_data['price_margin'])
        price_eur = btc_price + premium / 100 * btc_price

        offers.append(
            Offer(
                id=offer_data['_id'],
                exchange=Exchange.LNP2PBOT,
                amount=f'{offer_data['fiat_amount'] if offer_data['fiat_amount'] else f'{offer_data['min_amount']} - {offer_data['max_amount']}'} €',
                price_eur=price_eur,
                price_usd=price_eur * eur_dolar_rate,
                premium=float(offer_data['price_margin']),
                payment_methods=payment_methods,
                description=offer_data['description']
            )
        )

    return offers


async def fetch_offers_from_telegram(eur_dolar_rate: float, btc_price: float) -> list[Offer]:
    async with client:
        exchange_chat = await client.get_entity(config.lnp2pbot_channel_name)

        offers = []
        async for message in client.iter_messages(exchange_chat, search='#SELLEUR'):
            lines = message.text.splitlines()

            description = '\n'.join(lines[3:-7])

            if not (payment_methods := _find_payment_methods(description)):
                continue

            premium = flanautils.text_to_number(lines[-4])
            price_eur = btc_price + premium / 100 * btc_price

            offers.append(
                Offer(
                    id=lines[-1].strip(':'),
                    exchange=Exchange.LNP2PBOT,
                    amount=lines[2],
                    price_eur=price_eur,
                    price_usd=price_eur * eur_dolar_rate,
                    premium=premium,
                    payment_methods=payment_methods,
                    description=description
                )
            )

    return offers
