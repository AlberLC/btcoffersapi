from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from config import config

database_client = AsyncMongoClient(username=config.mongo_username, password=config.mongo_password, tz_aware=True)
database: AsyncDatabase = database_client[config.database_name]
