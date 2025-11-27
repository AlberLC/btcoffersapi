import asyncio
import json

from fastapi import WebSocket, WebSocketDisconnect, websockets

from config import config
from database.repositories.offer_repository import OfferRepository


async def notify_offers(
    websocket: WebSocket,
    offer_repository: OfferRepository,
    chat_id: int,
    query: dict[str, float]
) -> None:
    while not (offers := await offer_repository.get(**query)):
        await asyncio.sleep(config.fetch_offers_every.total_seconds())

        if websocket.client_state == websockets.WebSocketState.DISCONNECTED:
            return

    try:
        await websocket.send_text(
            json.dumps(
                {
                    'chat_id': chat_id,
                    'offers': [offer.model_dump() for offer in offers]
                }
            )
        )
    except WebSocketDisconnect:
        pass
