from typing import Annotated, Self

import aiohttp
from pydantic import ConfigDict, PlainValidator

import utils
from api.schemas.bases import ObjectIdModel
from api.schemas.nostr_events import NostrOfferEvent
from config import config
from enums import Exchange, PaymentMethod
from services import payment_method_service
from services.yadio_cache_service import YadioCache


class Offer(ObjectIdModel):
    exchange: Exchange
    id: str
    fiat_amount: str
    price_eur: float
    price_usd: float
    premium: float
    payment_methods: list[PaymentMethod]
    author: str | None = None
    trades: int | None = None
    rating: float | None = None
    url: str | None = None
    description: Annotated[str, PlainValidator(str.strip)] | None = None
    original_sat_amount: int | None = None
    original_fiat_amount: float | None = None
    original_price_eur: float | None = None

    model_config = ConfigDict(use_enum_values=True)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Offer):
            return NotImplemented

        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    async def check_exists(self, session: aiohttp.ClientSession, delay: float = 0.5) -> bool:
        return self.id in html if self.url and (html := await utils.fetch_html(self.url, session, delay)) else False

    def refresh_prices(self, yadio_cache: YadioCache) -> None:
        if self.original_sat_amount and self.original_fiat_amount:
            self.price_eur = float(self.original_fiat_amount) / (self.original_sat_amount / config.sats_per_btc)
            self.price_usd = self.price_eur * yadio_cache.eur_dolar_rate
            self.premium = (self.price_eur / yadio_cache.btc_price - 1) * 100
        elif self.original_price_eur:
            self.price_usd = self.original_price_eur * yadio_cache.eur_dolar_rate
            self.premium = (self.original_price_eur / yadio_cache.btc_price - 1) * 100
        else:
            self.price_eur = (1 + self.premium / 100) * yadio_cache.btc_price
            self.price_usd = self.price_eur * yadio_cache.eur_dolar_rate


class HodlHodlOffer(Offer):
    @classmethod
    def from_data(cls, data: dict, yadio_cache: YadioCache) -> Self | None:
        offer_payment_method_ids = {
            payment_method_data['payment_method_id']
            for payment_method_data in data['payment_method_instructions']
        }
        payment_methods = []

        for payment_method, payment_method_ids in config.hodlhodl_payment_methods_ids.items():
            if payment_method_ids & offer_payment_method_ids:
                payment_methods.append(payment_method)

        if not payment_methods:
            return

        offer_id = data['id']

        if data['min_amount'] == data['max_amount']:
            fiat_amount_value = data['min_amount']
        else:
            fiat_amount_value = f'{data['min_amount']} - {data['max_amount']}'

        return cls(
            exchange=Exchange.HODLHODL,
            id=offer_id,
            fiat_amount=f'{fiat_amount_value} €',
            price_eur=float(data['price']),
            price_usd=float(data['price']) * yadio_cache.eur_dolar_rate,
            premium=(float(data['price']) / yadio_cache.btc_price - 1) * 100,
            payment_methods=payment_methods,
            author=data['trader']['login'],
            trades=data['trader']['trades_count'],
            rating=data['trader']['rating'],
            url=f'{config.hodlhodl_offers_web_base_url}/{offer_id}',
            description=data['description']
        )


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
                fiat_amount_value = nostr_offer_event.tags['fa']
            else:
                fiat_amount_value = f'{nostr_offer_event.tags['fa'][0]} - {nostr_offer_event.tags['fa'][1]}'

            if original_sat_amount := int(nostr_offer_event.tags['amt']) or None:
                original_fiat_amount = float(fiat_amount_value)
                # noinspection PyUnboundLocalVariable
                price_eur = original_fiat_amount / (original_sat_amount / config.sats_per_btc)
                premium = (price_eur / yadio_cache.btc_price - 1) * 100
            else:
                original_fiat_amount = None
                premium = float(nostr_offer_event.tags['premium'])
                price_eur = (1 + premium / 100) * yadio_cache.btc_price

            rating, _, trades = nostr_offer_event.tags['rating']
            url = nostr_offer_event.tags['source']

            return cls(
                exchange=Exchange.LNP2PBOT,
                id=nostr_offer_event.tags['d'],
                fiat_amount=f'{fiat_amount_value} €',
                price_eur=price_eur,
                price_usd=price_eur * yadio_cache.eur_dolar_rate,
                premium=premium,
                payment_methods=payment_methods,
                author=await cls._fetch_offer_author(url, session),
                trades=int(trades),
                rating=float(rating) / config.lnp2pbot_max_rating,
                url=url,
                description=description,
                original_sat_amount=original_sat_amount,
                original_fiat_amount=original_fiat_amount
            )
        except KeyError, ValueError:
            pass
