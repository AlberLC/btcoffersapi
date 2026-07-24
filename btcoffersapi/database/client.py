from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from config import config

client = AsyncMongoClient(username=config.mongo_username, password=config.mongo_password, tz_aware=True)
database: AsyncDatabase = client[config.database_name]
