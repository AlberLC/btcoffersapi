import asyncio
import json

import aiohttp
import aiohttp_socks
from fastapi import status

from api.schemas.enums import Exchange
from api.schemas.offer import Offer
from config import config


async def _get_coordinators_urls(session: aiohttp.ClientSession) -> list[str]:
    for _ in range(config.robosats_coordinators_urls_attempts):
        try:
            async with session.get(config.robosats_coordinators_url) as response:
                return [
                    coordinator_url for coordinator in (await response.json(content_type=None)).values()
                    if (coordinator_url := coordinator['mainnet']['onion'])
                ]
        except (AttributeError, json.JSONDecodeError, aiohttp.ClientConnectionError):
            await asyncio.sleep(1)

    return []


async def fetch_offers(session: aiohttp.ClientSession, eur_dolar_rate: float) -> list[Offer]:
    offers = []

    if not (coordinators_urls := await _get_coordinators_urls(session)):
        return offers

    connector = aiohttp_socks.ProxyConnector.from_url(config.tor_proxy_url)
    async with aiohttp.ClientSession(connector=connector, headers={'Accept': 'application/json'}) as tor_session:
        params = {
            'currency': 2,
            'type': 1
        }
        for coordinator_url in coordinators_urls:
            await asyncio.sleep(config.tor_request_delay)

            try:
                async with tor_session.get(
                    config.robosats_coordinator_api_endpoint_template.format(coordinator_url), params=params
                ) as response:
                    if response.status == status.HTTP_404_NOT_FOUND:
                        continue

                    offers_data = await response.json()
            except (TimeoutError, aiohttp_socks.ProxyError, aiohttp.ContentTypeError, aiohttp.ServerDisconnectedError):
                continue

            for offer_data in offers_data:
                payment_methods = []
                for payment_method_name, payment_method in config.robosats_payment_methods.items():
                    if payment_method_name in offer_data['payment_method']:
                        payment_methods.append(payment_method)

                if not payment_methods:
                    continue

                offers.append(
                    Offer(
                        id=str(offer_data['id']),
                        exchange=Exchange.ROBOSATS,
                        author=offer_data['maker_nick'],
                        amount=f'{f'{float(offer_data['amount']):.2f}' if offer_data['amount'] else f'{float(offer_data['min_amount']):.2f} - {float(offer_data['max_amount']):.2f}'} €',
                        price_eur=float(offer_data['price']),
                        price_usd=float(offer_data['price']) * eur_dolar_rate,
                        premium=float(offer_data['premium']),
                        payment_methods=payment_methods
                    )
                )

    return offers
