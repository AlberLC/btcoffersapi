from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from btcoffersapi.config import config


def create_object_id(id: str) -> ObjectId:
    try:
        return ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f'{id} is not a valid ObjectId')


client = AsyncIOMotorClient(username=config.mongo_username, password=config.mongo_password)
database: AsyncIOMotorDatabase = client[config.database_name]
