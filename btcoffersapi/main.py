import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from api.routers import offers
from config import config


@asynccontextmanager
async def lifespan(_: FastAPI):
    database_lock = asyncio.Lock()
    # asyncio.create_task(offer_fetcher.fetch_offers(database_lock))
    yield {'database_lock': database_lock, 'notification_tasks': defaultdict(lambda: None)}


app = FastAPI(lifespan=lifespan)
app.include_router(offers.router)

if __name__ == '__main__':
    uvicorn.run('main:app', host=config.api_host, port=config.api_port, reload=True)
