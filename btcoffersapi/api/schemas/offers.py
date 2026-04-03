from typing import Annotated, Self

import aiohttp
from pydantic import BaseModel, ConfigDict, PlainValidator

import utils
from api.schemas.nostr_events import NostrOfferEvent
from config import config
from enums import Exchange, PaymentMethod
from services import payment_method_service
from services.yadio_cache_service import YadioCache


class Offer(BaseModel):
    exchange: Exchange
    id: str
    amount: str
    price_eur: float
    price_usd: float
    premium: float
    payment_methods: list[PaymentMethod]
    author: str | None = None
    trades: int | None = None
    rating: float | None = None
    url: str | None = None
    description: Annotated[str, PlainValidator(str.strip)] | None = None

    model_config = ConfigDict(use_enum_values=True)

    async def check_exists(self, session: aiohttp.ClientSession, delay: float = 0.5) -> bool:
        return self.id in html if self.url and (html := await utils.fetch_html(self.url, session, delay)) else False


class LnP2pBotOffer(Offer):
    @staticmethod
    async def _fetch_offer_author(url: str, session: aiohttp.ClientSession, delay: float = 0.5) -> str | None:
        if (
            (html := await utils.fetch_html(url, session, delay))
            and
            (match := config.lnp2pbot_html_author_pattern.search(html))
        ):
            return match.group(1)

    @classmethod
    async def from_nostr_offer_event(
        cls,
        nostr_offer_event: NostrOfferEvent,
        yadio_cache: YadioCache,
        session: aiohttp.ClientSession
    ) -> Self | None:
        try:
            description = nostr_offer_event.tags['pm']

            if not (payment_methods := payment_method_service.find_payment_methods(description)):
                return

            if isinstance(nostr_offer_event.tags['fa'], str):
                amount_value = nostr_offer_event.tags['fa']
            else:
                amount_value = f'{nostr_offer_event.tags['fa'][0]} - {nostr_offer_event.tags['fa'][1]}'

            if sats := int(nostr_offer_event.tags['amt']):
                price_eur = float(amount_value) / (sats / config.sats_per_btc)
                premium = (price_eur / yadio_cache.btc_price - 1) * 100
            else:
                premium = float(nostr_offer_event.tags['premium'])
                price_eur = (1 + premium / 100) * yadio_cache.btc_price

            rating, _, trades = nostr_offer_event.tags['rating']
            url = nostr_offer_event.tags['source']

            return Offer(
                exchange=Exchange.LNP2PBOT,
                id=nostr_offer_event.tags['d'],
                amount=f'{amount_value} €',
                price_eur=price_eur,
                price_usd=price_eur * yadio_cache.eur_dolar_rate,
                premium=premium,
                payment_methods=payment_methods,
                author=await cls._fetch_offer_author(url, session),
                trades=int(trades),
                rating=float(rating) / config.lnp2pbot_max_rating,
                url=url,
                description=description
            )
        except KeyError, ValueError:
            pass
