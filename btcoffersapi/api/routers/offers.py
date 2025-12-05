import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status

from api.schemas.offers_data import OfferData, OffersData
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

        if notifier_task := notification_tasks.get(data['chat_id']):
            notifier_task.cancel()

        if data['action'] == 'start':
            notification_tasks[data['chat_id']] = asyncio.create_task(
                offer_notifier.notify_offers(websocket, offer_repository, data['chat_id'], data['query'])
            )


@router.get('')
async def get_offers(
    offer_repository: Annotated[OfferRepository, Depends(OfferRepository)],
    offers_params: Annotated[OffersParams, Query()]
) -> OffersData:
    return await offer_repository.get(
        offers_params.max_price_eur,
        offers_params.max_price_usd,
        offers_params.max_premium,
        offers_params.payment_methods,
        offers_params.exchanges,
        offers_params.ignore_authors,
        offers_params.limit
    )


@router.get('/{id}')
async def get_offer(id: str, offer_repository: Annotated[OfferRepository, Depends(OfferRepository)]) -> OfferData:
    if not (offer := await offer_repository.get_by_id(id)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Offer not found')

    return offer
