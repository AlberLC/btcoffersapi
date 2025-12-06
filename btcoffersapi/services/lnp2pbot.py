import asyncio

import aiohttp
import flanautils
import playwright.async_api

from api.schemas.enums import Exchange, PaymentMethod
from api.schemas.offer import Offer
from config import config


def _find_payment_methods(text: str) -> list[PaymentMethod]:
    payment_methods = []
    normalized_description = flanautils.remove_accents(text.lower())

    for payment_method, payment_method_names in config.lnp2pbot_payment_method_keywords.items():
        if payment_method in payment_methods:
            continue

        for payment_method_name in payment_method_names:
            if payment_method_name in normalized_description:
                if payment_method_name == 'instant sepa':
                    normalized_description = normalized_description.replace('instant sepa', '')

                if payment_method_name == 'sepa instant':
                    normalized_description = normalized_description.replace('sepa instant', '')

                payment_methods.append(payment_method)
                break

    return payment_methods


async def _get_web_message_elements(page: playwright.async_api.Page) -> list[playwright.async_api.Locator]:
    message_selector = 'section.tgme_channel_history.js-message_history div.tgme_widget_message_text'
    loading_selector = '.tme_messages_more'

    await page.wait_for_selector(message_selector)

    previous_message_elements = await page.locator(message_selector).all()

    while True:
        await _scroll_web_to_top(page)
        await asyncio.sleep(1)

        try:
            await page.wait_for_selector(loading_selector, timeout=1000)
        except playwright.async_api.TimeoutError:
            return previous_message_elements

        message_elements = await page.locator(message_selector).all()

        if len(message_elements) == len(previous_message_elements):
            return message_elements

        previous_message_elements = message_elements


async def _scroll_web_to_top(page: playwright.async_api.Page) -> None:
    await page.evaluate('window.scrollTo(0, 0)')


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
                amount=f'{f'{float(offer_data['fiat_amount']):.2f}' if offer_data['fiat_amount'] else f'{float(offer_data['min_amount']):.2f} - {float(offer_data['max_amount']):.2f}'} €',
                price_eur=price_eur,
                price_usd=price_eur * eur_dolar_rate,
                premium=float(offer_data['price_margin']),
                payment_methods=payment_methods,
                description=offer_data['description']
            )
        )

    return offers


async def fetch_offers_from_web(eur_dolar_rate: float, btc_price: float) -> list[Offer]:
    for _ in range(config.lnp2pbot_scraping_attempts):
        try:
            async with playwright.async_api.async_playwright() as playwright_:
                async with await playwright_.chromium.launch() as browser:
                    page = await browser.new_page()

                    await page.goto(config.lnp2pbot_web_url)
                    await page.wait_for_load_state('networkidle')

                    offers = []

                    for element in await _get_web_message_elements(page):
                        lines = (await element.inner_text()).splitlines()

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
        except playwright.async_api.TimeoutError:
            await asyncio.sleep(1)
        else:
            return offers

    return []
