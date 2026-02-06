import multiprocessing
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI

from api.routers import offers
from config import config
from workers import offer_fetcher


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[dict[str, Any]]:
    yield {'notification_tasks': {}}


app = FastAPI(lifespan=lifespan, root_path='/btcoffersapi')
app.include_router(offers.router)

if __name__ == '__main__':
    multiprocessing.Process(target=offer_fetcher.run, daemon=True).start()
    uvicorn.run('main:app', host=config.api_host, port=config.api_port)
