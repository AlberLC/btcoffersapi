import flanautils
from telethon import TelegramClient
from telethon.sessions import StringSession

from btcoffersapi.api.schemas.enums import Exchange
from btcoffersapi.api.schemas.offer import Offer
from btcoffersapi.config import config

client = TelegramClient(StringSession(config.telegram_user_session), config.telegram_api_id, config.telegram_api_hash)


async def fetch_offers(eur_dolar_rate: float, btc_price: float) -> list[Offer]:
    async with client:
        exchange_chat = await client.get_entity('p2plightning')

        offers = []
        async for message in client.iter_messages(exchange_chat, search='#SELLEUR'):
            lines = message.text.splitlines()

            description = '\n'.join(lines[3:-7])

            payment_methods = []
            normalized_description = flanautils.remove_accents(description.lower())
            for payment_method_name, payment_method in config.lnp2pbot_payment_methods.items():
                if payment_method_name in normalized_description:
                    if payment_method_name == 'instant sepa':
                        normalized_description = normalized_description.replace('instant sepa', '')

                    if payment_method_name == 'sepa instant':
                        normalized_description = normalized_description.replace('sepa instant', '')

                    payment_methods.append(payment_method)

            if not payment_methods:
                continue

            premium = flanautils.text_to_number(lines[-4])
            price_eur = btc_price + premium / 100 * btc_price

            offers.append(
                Offer(
                    id=lines[-1],
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
