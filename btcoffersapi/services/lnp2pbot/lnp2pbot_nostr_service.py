import asyncio
import datetime
import json
from asyncio import Task
from collections.abc import AsyncGenerator

import aiohttp
import pymongo.errors

from api.schemas.nostr_events import NostrOfferEvent
from api.schemas.offers import LnP2pBotOffer, Offer
from config import config
from database.locks import database_lock
from database.repositories.offer_repository import OfferRepository
from enums import Exchange, NostrMessageType
from services.yadio_cache_service import YadioCache


async def _fetch_old_offers(yadio_cache: YadioCache, session: aiohttp.ClientSession) -> list[Offer]:
    events = {}

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(config.lnp2pbot_nostr_timeout)) as nostr_session:
        await asyncio.gather(
            *(_merge_relay_events(realy_url, events, nostr_session) for realy_url in config.lnp2pbot_nostr_relay_urls)
        )

    sorted_events = sorted(events.items(), key=lambda item: item[1].created_at)
    pending_events = {}

    for event_id, event in sorted_events:
        offer_id = event.tags['d']

        if event.tags['s'] == 'pending':
            pending_events[offer_id] = event
        elif offer_id in pending_events:
            del pending_events[offer_id]

    offers = []

    for event in pending_events.values():
        if offer := await LnP2pBotOffer.from_nostr_offer_event(event, yadio_cache, session):
            offers.append(offer)

    return offers


async def _iter_relay_events(
    websocket: aiohttp.ClientWebSocketResponse,
    since: int | None = None,
    until: int | None = None,
    keep_listening: bool = False
) -> AsyncGenerator[NostrOfferEvent]:
    filter_ = {
        'authors': [config.lnp2pbot_nostr_public_key],
        'kinds': [config.lnp2pbot_nostr_event_kind],
        'limit': config.lnp2pbot_nostr_events_limit
    }

    if since:
        filter_['since'] = since

    if until:
        filter_['until'] = until

    await websocket.send_json([NostrMessageType.REQ.value, config.lnp2pbot_nostr_subscription_id, filter_])

    async for message in websocket:
        if message.type in {aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR}:
            break

        if message.type != aiohttp.WSMsgType.TEXT:
            continue

        message_data = json.loads(message.data)
        message_type = NostrMessageType(message_data[0])

        if (
            message_type in {NostrMessageType.CLOSE, NostrMessageType.NOTICE}
            or
            message_type is NostrMessageType.EOSE and not keep_listening
        ):
            break
        elif message_type is not NostrMessageType.EVENT:
            continue

        yield NostrOfferEvent(message_data[2])

    await websocket.send_json([NostrMessageType.CLOSE.value, config.lnp2pbot_nostr_subscription_id])


async def _listen_relay_events(
    relay_url: str,
    now: datetime.datetime,
    yadio_cache: YadioCache,
    offer_repository: OfferRepository,
    session: aiohttp.ClientSession,
    nostr_session: aiohttp.ClientSession
) -> None:
    while True:
        try:
            async with nostr_session.ws_connect(relay_url, heartbeat=config.lnp2pbot_nostr_ws_heartbeat) as websocket:
                async for event in _iter_relay_events(websocket, since=int(now.timestamp()), keep_listening=True):
                    if not event.is_valid:
                        continue

                    async with database_lock():
                        if event.tags['s'] != 'pending':
                            await offer_repository.delete_one({'id': event.tags['d']})
                            continue

                        if (
                            await offer_repository.get_one({'id': event.tags['d']})
                            or
                            not (offer := await LnP2pBotOffer.from_nostr_offer_event(event, yadio_cache, session))
                        ):
                            continue

                        try:
                            await offer_repository.insert_one(offer)
                        except pymongo.errors.DuplicateKeyError:
                            pass
        except TimeoutError, aiohttp.ClientError:
            await asyncio.sleep(config.lnp2pbot_nostr_relay_reconnect_sleep)


async def _merge_relay_events(
    relay_url: str,
    events: dict[str, NostrOfferEvent],
    session: aiohttp.ClientSession
) -> None:
    oldest_created_at: int | None = None
    previous_oldest_created_at: int | None = None

    for attempt in range(config.lnp2pbot_nostr_fetch_attempts - 1, -1, -1):
        try:
            async with session.ws_connect(relay_url, heartbeat=config.lnp2pbot_nostr_ws_heartbeat) as websocket:
                while True:
                    page_events_count = 0

                    async for event in _iter_relay_events(websocket, until=oldest_created_at):
                        if event.is_valid and event.id not in events:
                            events[event.id] = event

                        if event.created_at and (not oldest_created_at or event.created_at < oldest_created_at):
                            oldest_created_at = event.created_at

                        page_events_count += 1

                    if page_events_count < config.lnp2pbot_nostr_events_limit or not oldest_created_at:
                        return

                    if oldest_created_at == previous_oldest_created_at:
                        oldest_created_at -= 1

                    previous_oldest_created_at = oldest_created_at

                    await asyncio.sleep(config.lnp2pbot_nostr_pagination_sleep)
        except TimeoutError, aiohttp.ClientError:
            if attempt:
                await asyncio.sleep(1)


async def clean_up_invalid_offers(
    lnp2pbot_old_offer_sync_task: Task,
    offer_repository: OfferRepository,
    session: aiohttp.ClientSession
) -> None:
    await lnp2pbot_old_offer_sync_task

    for offer in await offer_repository.get_offers(exchanges=(Exchange.LNP2PBOT,)):
        if not await offer.check_exists(session):
            await offer_repository.delete_one({'id': offer.id})


async def listen_new_offers(
    lnp2pbot_old_offer_sync_task: Task,
    yadio_cache: YadioCache,
    offer_repository: OfferRepository,
    session: aiohttp.ClientSession
) -> None:
    await lnp2pbot_old_offer_sync_task

    now = datetime.datetime.now(datetime.UTC)

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(config.lnp2pbot_nostr_timeout)) as nostr_session:
        await asyncio.gather(
            *(
                _listen_relay_events(realy_url, now, yadio_cache, offer_repository, session, nostr_session)
                for realy_url in config.lnp2pbot_nostr_relay_urls
            )
        )


async def sync_old_offers(
    yadio_cache: YadioCache,
    offer_repository: OfferRepository,
    session: aiohttp.ClientSession
) -> None:
    offers = await _fetch_old_offers(yadio_cache, session)

    async with database_lock():
        await offer_repository.delete({'exchange': 'lnp2pBot'})
        await offer_repository.insert(offers)
