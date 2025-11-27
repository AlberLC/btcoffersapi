import asyncio
import datetime
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from config import config
from database.client import database


@asynccontextmanager
async def database_lock(should_lock: bool = True) -> AsyncIterator[None]:
    lock_collection = database['locks']

    if should_lock:
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

    if should_lock:
        await lock_collection.delete_one({'_id': 'offers_lock'})
