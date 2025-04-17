from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from btcoffersapi.api.routers import offers
from btcoffersapi.config import config


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield {'notification_tasks': {}}


app = FastAPI(lifespan=lifespan, root_path='/btcoffersapi')
app.include_router(offers.router)

if __name__ == '__main__':
    uvicorn.run('main:app', host=config.api_host, port=config.api_port)
