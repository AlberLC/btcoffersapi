import asyncio

import fastapi.encoders
from fastapi import WebSocket, WebSocketDisconnect, websockets

from api.schemas.enums import Exchange, PaymentMethod
from config import config
from database.repositories.offer_repository import OfferRepository


async def notify_offers(
    websocket: WebSocket,
    offer_repository: OfferRepository,
    chat_id: int,
    raw_query: dict[str, float | list[str]]
) -> None:
    query = {}

    for k, v in raw_query.items():
        if k == 'payment_methods':
            v = [PaymentMethod(payment_method) for payment_method in raw_query['payment_methods']]
        elif k == 'exchanges':
            v = [Exchange(exchange) for exchange in raw_query['exchanges']]

        query[k] = v

    while not (offers_data := await offer_repository.get(**query)):
        await asyncio.sleep(config.offers_fetch_sleep)

        if websocket.client_state == websockets.WebSocketState.DISCONNECTED:
            return

    try:
        await websocket.send_json(fastapi.encoders.jsonable_encoder({'chat_id': chat_id, 'offers_data': offers_data}))
    except WebSocketDisconnect:
        pass
