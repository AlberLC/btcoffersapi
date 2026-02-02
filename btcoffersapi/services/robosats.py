import asyncio
import json

import aiohttp
import aiohttp_socks
from fastapi import status

from api.schemas.enums import Exchange, PaymentMethod
from api.schemas.offer import Offer
from config import config


def _find_payment_methods(offer_payment_method_names: str) -> list[PaymentMethod]:
    payment_methods = []

    normalized_offer_payment_method_names = offer_payment_method_names.lower()

    for payment_method, payment_method_names in config.payment_method_keywords.items():
        if payment_method in payment_methods:
            continue

        for payment_method_name in payment_method_names:
            if payment_method_name in normalized_offer_payment_method_names:
                payment_methods.append(payment_method)
                break

    return payment_methods


async def _get_coordinators_urls(session: aiohttp.ClientSession) -> list[str]:
    for _ in range(config.robosats_coordinators_urls_attempts):
        try:
            async with session.get(config.robosats_coordinators_url) as response:
                return [
                    coordinator_url for coordinator_data in (await response.json(content_type=None)).values()
                    if (coordinator_url := coordinator_data['mainnet']['onion'])
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
        params = {'currency': 2, 'type': 1}

        for coordinator_url in coordinators_urls:
            await asyncio.sleep(config.tor_request_sleep)

            try:
                async with tor_session.get(
                    config.robosats_coordinator_api_endpoint_template.format(coordinator_url), params=params
                ) as response:
                    if response.status == status.HTTP_404_NOT_FOUND:
                        continue

                    offers_data = await response.json()
            except (
                    TimeoutError,
                    aiohttp.ContentTypeError,
                    aiohttp.ServerDisconnectedError,
                    aiohttp_socks.ProxyError,
                    aiohttp_socks.ProxyTimeoutError
            ):
                continue

            for offer_data in offers_data:
                if not (payment_methods := _find_payment_methods(offer_data['payment_method'])):
                    continue

                if offer_data['amount']:
                    amount_value = f'{float(offer_data['amount']):.2f}'
                else:
                    amount_value = f'{float(offer_data['min_amount']):.2f} - {float(offer_data['max_amount']):.2f}'

                offers.append(
                    Offer(
                        id=str(offer_data['id']),
                        exchange=Exchange.ROBOSATS,
                        author=offer_data['maker_nick'],
                        amount=f'{amount_value} €',
                        price_eur=float(offer_data['price']),
                        price_usd=float(offer_data['price']) * eur_dolar_rate,
                        premium=float(offer_data['premium']),
                        payment_methods=payment_methods
                    )
                )

    return offers
