import asyncio
import json

from fastapi import WebSocket

from btcoffersapi.config import config
from btcoffersapi.database.repositories.offer_repository import OfferRepository


async def notify_offers(
    websocket: WebSocket,
    offer_repository: OfferRepository,
    chat_id: int,
    query: dict[str, float]
) -> None:
    while not (offers := await offer_repository.get(**query)):
        await asyncio.sleep(config.fetch_offers_every.total_seconds())

    await websocket.send_text(
        json.dumps(
            {
                'chat_id': chat_id,
                'offers': [offer.model_dump() for offer in offers]
            }
        )
    )
