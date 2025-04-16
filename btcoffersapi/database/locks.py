import asyncio
import datetime
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from btcoffersapi.config import config
from btcoffersapi.database.client import database


@asynccontextmanager
async def database_lock(lock: bool = True) -> AsyncIterator[None]:
    lock_collection = database['locks']

    if lock:
        while await lock_collection.find_one(
            {'_id': 'offers_lock', 'until': {'$gte': datetime.datetime.now(datetime.timezone.utc)}}
        ):
            await asyncio.sleep(1)

        await lock_collection.update_one(
            {'_id': 'offers_lock'},
            {
                '$set': {
                    'until': datetime.datetime.now(datetime.timezone.utc) + config.database_lock_expiration
                }
            },
            upsert=True
        )

    yield

    if lock:
        await lock_collection.delete_one({'_id': 'offers_lock'})
