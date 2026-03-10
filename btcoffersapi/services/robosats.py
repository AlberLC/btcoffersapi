import asyncio
import json
import re

import aiohttp
import aiohttp_socks
from fastapi import status

from api.schemas.offer import Offer
from config import config
from enums import Exchange
from services import payment_method_service


async def fetch_robosats_url() -> str:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(config.robosats_readme_url) as response:
                text = await response.text()
    except TimeoutError, aiohttp.ClientError:
        return config.robosats_url
    else:
        return match.group() if (match := re.search(r'http://[a-zA-Z2-7]{56}\.onion', text)) else config.robosats_url


async def _get_coordinators_urls(session: aiohttp.ClientSession) -> dict[str, str]:
    for attempt in range(config.robosats_coordinators_urls_attempts - 1, -1, -1):
        try:
            async with session.get(config.robosats_coordinators_url) as response:
                return {
                    name: url for coordinator_data in (await response.json(content_type=None)).values()
                    if (name := coordinator_data['shortAlias']) and (url := coordinator_data['mainnet']['onion'])
                }
        except AttributeError, json.JSONDecodeError, aiohttp.ClientError:
            if attempt:
                await asyncio.sleep(1)

    return {}


async def fetch_offers(session: aiohttp.ClientSession, robosats_url: str, eur_dolar_rate: float) -> list[Offer]:
    if not (coordinators_urls := await _get_coordinators_urls(session)):
        return []

    connector = aiohttp_socks.ProxyConnector.from_url(config.tor_proxy_url)
    async with aiohttp.ClientSession(connector=connector, headers={'Accept': 'application/json'}) as tor_session:
        params = {'currency': 2, 'type': 1}

        offers = []

        for coordinator_name, coordinator_url in coordinators_urls.items():
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
                if not (payment_methods := payment_method_service.find_payment_methods(offer_data['payment_method'])):
                    continue

                offer_id = offer_data['id']

                if offer_data['amount']:
                    amount_value = f'{float(offer_data['amount']):.2f}'
                else:
                    amount_value = f'{float(offer_data['min_amount']):.2f} - {float(offer_data['max_amount']):.2f}'

                offers.append(
                    Offer(
                        id=str(offer_id),
                        exchange=Exchange.ROBOSATS,
                        amount=f'{amount_value} €',
                        price_eur=float(offer_data['price']),
                        price_usd=float(offer_data['price']) * eur_dolar_rate,
                        premium=float(offer_data['premium']),
                        payment_methods=payment_methods,
                        author=offer_data['maker_nick'],
                        url=f'{robosats_url}/order/{coordinator_name}/{offer_id}'
                    )
                )

    return offers
