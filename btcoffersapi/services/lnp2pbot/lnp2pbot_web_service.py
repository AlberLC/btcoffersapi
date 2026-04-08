import asyncio

import flanautils
import playwright.async_api

from api.schemas.offers import Offer
from config import config
from enums import Exchange
from services import payment_method_service


async def _get_web_message_elements(page: playwright.async_api.Page) -> list[playwright.async_api.Locator]:
    message_selector = 'section.tgme_channel_history.js-message_history div.tgme_widget_message_text'
    loading_selector = '.tme_messages_more'

    try:
        await page.wait_for_selector(message_selector, timeout=config.lnp2pbot_message_selector_timeout)
    except playwright.async_api.TimeoutError:
        return []

    previous_message_elements = await page.locator(message_selector).all()

    while True:
        await _scroll_web_to_top(page)
        await asyncio.sleep(1)

        try:
            await page.wait_for_selector(loading_selector, timeout=config.lnp2pbot_loading_selector_timeout)
        except playwright.async_api.TimeoutError:
            return previous_message_elements

        message_elements = await page.locator(message_selector).all()

        if len(message_elements) == len(previous_message_elements):
            return message_elements

        previous_message_elements = message_elements


async def _scroll_web_to_top(page: playwright.async_api.Page) -> None:
    await page.evaluate('window.scrollTo(0, 0)')


async def fetch_offers_from_web(eur_dolar_rate: float, btc_price: float) -> list[Offer]:
    for attempt in range(config.lnp2pbot_scrape_attempts - 1, -1, -1):
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

                        if not (payment_methods := payment_method_service.find_payment_methods(description)):
                            continue

                        premium = flanautils.text_to_number(lines[-4])
                        price_eur = btc_price + premium / 100 * btc_price

                        offers.append(
                            Offer(
                                exchange=Exchange.LNP2PBOT,
                                id=lines[-1].strip(':'),
                                fiat_amount=lines[2],
                                price_eur=price_eur,
                                price_usd=price_eur * eur_dolar_rate,
                                premium=premium,
                                payment_methods=payment_methods,
                                description=description
                            )
                        )
        except playwright.async_api.Error:
            if attempt:
                await asyncio.sleep(1)
        else:
            return offers

    return []
