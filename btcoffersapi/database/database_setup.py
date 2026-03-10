from config import config
from database.client import database


async def ensure_indexes_exist() -> None:
    for collection_name, index_configs in config.indexes.items():
        collection = database[collection_name]
        index_names = [index['name'] async for index in await collection.list_indexes()]

        for index_config in index_configs:
            if index_config['name'] in index_names:
                continue

            await collection.create_index(**index_config)


async def initialize_database() -> None:
    await ensure_indexes_exist()
