import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from database.repositories.offer_repository import OfferRepository
from services import offer_notifier_service

router = APIRouter(prefix='/ws', tags=['ws'])


@router.websocket('/offers/notifications')
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
