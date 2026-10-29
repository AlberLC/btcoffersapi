from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase

from config import config
from exceptions import DatabaseNotInitializedError

_database: AsyncDatabase | None = None
_database_client: AsyncMongoClient | None = None


async def close_database_client() -> None:
    global _database, _database_client

    if _database_client is None:
        return

    await _database_client.close()

    _database = None
    _database_client = None


def get_collection(collection_name: str) -> AsyncCollection:
    if _database is None:
        raise DatabaseNotInitializedError

    return _database[collection_name]


def get_database() -> AsyncDatabase:
    if _database is None:
        raise DatabaseNotInitializedError

    return _database


def get_database_client() -> AsyncMongoClient:
    if _database_client is None:
        raise DatabaseNotInitializedError

    return _database_client


def initialize_database_client() -> None:
    global _database, _database_client

    if _database_client is not None:
        return

    database_client = AsyncMongoClient(username=config.mongo_username, password=config.mongo_password, tz_aware=True)
    _database_client = database_client
    _database = database_client[config.database_name]
