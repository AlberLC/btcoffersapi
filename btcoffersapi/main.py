import multiprocessing
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI

from api.routers import offers_router, websockets_router
from config import config
from database import database_setup
from workers import offer_fetcher


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[dict[str, Any]]:
    await database_setup.initialize_database()

    yield {'notification_tasks': {}}


app = FastAPI(lifespan=lifespan, root_path=config.api_root, root_path_in_servers=False)
app.include_router(offers_router.router)
app.include_router(websockets_router.router)

if __name__ == '__main__':
    multiprocessing.Process(target=offer_fetcher.run, daemon=True).start()
    uvicorn.run('main:app', host=config.api_host, port=config.api_port)
