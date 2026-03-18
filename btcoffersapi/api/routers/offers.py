import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

from api.schemas.dated_offers import DatedOffer, DatedOffers
from api.schemas.offers_params import OffersParams
from database.repositories.offer_repository import OfferRepository
from services import dated_offer_service, offer_notifier_service

router = APIRouter(prefix='/offers', tags=['offers'])


@router.get('')
async def get_offers(
    offers_params: Annotated[OffersParams, Query()],
    offer_repository: Annotated[OfferRepository, Depends(OfferRepository)]
) -> DatedOffers:
    return await dated_offer_service.get_dated_offers(
        offer_repository,
        offers_params.max_price_eur,
        offers_params.max_price_usd,
        offers_params.max_premium,
        offers_params.payment_methods,
        offers_params.exchanges,
        offers_params.ignore_authors,
        offers_params.limit
    )


@router.get('/{id}')
async def get_offer(id: str, offer_repository: Annotated[OfferRepository, Depends(OfferRepository)]) -> DatedOffer:
    return await dated_offer_service.get_dated_offer(id, offer_repository)


@router.websocket('/ws/notifications')
async def handle_offer_notification(
    offer_repository: Annotated[OfferRepository, Depends(OfferRepository)],
    websocket: WebSocket
) -> None:
    await websocket.accept()

    notification_tasks = websocket.state.notification_tasks

    while True:
        try:
            data = await websocket.receive_json()
        except WebSocketDisconnect:
            break

        if notifier_task := notification_tasks.get(data['chat_id']):
            notifier_task.cancel()

        if data['action'] == 'start':
            notification_tasks[data['chat_id']] = asyncio.create_task(
                offer_notifier_service.notify_offers(data['chat_id'], data['query'], offer_repository, websocket)
            )
