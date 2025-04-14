import asyncio
import json

from fastapi import WebSocket

from config import config
from database.repositories.offer_repository import OfferRepository


async def notify_offers(
    websocket: WebSocket,
    offer_repository: OfferRepository,
    chat_id: int,
    max_price_eur: float
) -> None:
    while not (offers := await offer_repository.get(max_price_eur, lock=websocket.state.database_lock)):
        await asyncio.sleep(config.fetch_offers_every.total_seconds())

    await websocket.send_text(
        json.dumps(
            {
                'chat_id': chat_id,
                'offers': [offer.model_dump() for offer in offers]
            }
        )
    )
