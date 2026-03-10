import asyncio

import fastapi.encoders
from fastapi import WebSocket, WebSocketDisconnect, websockets

from config import config
from database.repositories.offer_repository import OfferRepository
from enums import Exchange, PaymentMethod
from services import dated_offer_service


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

    while not (dated_offers := await dated_offer_service.get_dated_offers(offer_repository, **query)):
        await asyncio.sleep(config.offers_fetch_sleep)

        if websocket.client_state == websockets.WebSocketState.DISCONNECTED:
            return

    try:
        await websocket.send_json(fastapi.encoders.jsonable_encoder({'chat_id': chat_id, 'dated_offers': dated_offers}))
    except WebSocketDisconnect:
        pass
