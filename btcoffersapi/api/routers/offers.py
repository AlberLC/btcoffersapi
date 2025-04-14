import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect, status

from api.schemas.offer import Offer
from api.schemas.offers_params import OffersParams
from database.repositories.offer_repository import OfferRepository
from services import offer_notifier

router = APIRouter(prefix='/offers', tags=['offers'])


@router.websocket('')
async def websocket_endpoint(
    websocket: WebSocket,
    offer_repository: Annotated[OfferRepository, Depends(OfferRepository)]
) -> None:
    await websocket.accept()

    notification_tasks = websocket.state.notification_tasks

    while True:
        try:
            data = await websocket.receive_json()
        except WebSocketDisconnect:
            break

        if notifier_task := notification_tasks[data['chat_id']]:
            notifier_task.cancel()

        if data['action'] == 'start':
            notification_tasks[data['chat_id']] = asyncio.create_task(
                offer_notifier.notify_offers(websocket, offer_repository, data['chat_id'], float(data['max_price_eur']))
            )


@router.get('')
async def get_offers(
    request: Request,
    offer_repository: Annotated[OfferRepository, Depends(OfferRepository)],
    offers_params: Annotated[OffersParams, Query()]
) -> list[Offer]:
    return await offer_repository.get(
        offers_params.max_price_eur,
        offers_params.max_price_usd,
        offers_params.max_premium,
        offers_params.payment_method,
        offers_params.exchange,
        request.state.database_lock
    )


@router.get('/{id}')
async def get_offer(
    request: Request,
    id: str,
    offer_repository: Annotated[OfferRepository, Depends(OfferRepository)]
) -> Offer:
    if offer := await offer_repository.get_by_id(id, request.state.database_lock):
        return offer

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Offer not found')
