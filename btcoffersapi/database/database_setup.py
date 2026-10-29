from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from pymongo.asynchronous.database import AsyncDatabase

from config import config
from database import database_client


async def ensure_indexes_exist(database: AsyncDatabase) -> None:
    for collection_name, index_configs in config.indexes.items():
        collection = database[collection_name]
        index_names = {index['name'] async for index in await collection.list_indexes()}

        for index_config in index_configs:
            index_name = index_config['name']

            if index_name not in index_names:
                await collection.create_index(**index_config)
                index_names.add(index_name)


async def ensure_schema() -> None:
    try:
        database_client.initialize_database_client()

        await ensure_indexes_exist(database_client.get_database())
    finally:
        await database_client.close_database_client()


@asynccontextmanager
async def initialize_database() -> AsyncGenerator[None]:
    try:
        database_client.initialize_database_client()

        yield
    finally:
        await database_client.close_database_client()
