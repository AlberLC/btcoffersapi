import asyncio
import json

import fastapi.encoders
from fastapi import WebSocket, WebSocketDisconnect, websockets

from config import config
from database.repositories.offer_repository import OfferRepository


async def notify_offers(
    websocket: WebSocket,
    offer_repository: OfferRepository,
    chat_id: int,
    query: dict[str, float]
) -> None:
    while not (offers_data := await offer_repository.get(**query)):
        await asyncio.sleep(config.offers_fetch_sleep)

        if websocket.client_state == websockets.WebSocketState.DISCONNECTED:
            return

    try:
        await websocket.send_text(
            json.dumps({'chat_id': chat_id, 'offers_data': fastapi.encoders.jsonable_encoder(offers_data)})
        )
    except WebSocketDisconnect:
        pass
