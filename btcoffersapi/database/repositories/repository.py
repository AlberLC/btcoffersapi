import typing
from collections.abc import Iterable

from motor.motor_asyncio import AsyncIOMotorCollection


class Repository:
    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        self._collection = collection

    async def delete(self, id: str) -> None:
        await self._collection.delete_one({'id': id})

    async def delete_many(self, filter: dict) -> None:
        await self._collection.delete_many(filter)

    async def insert(self, item) -> typing.Any:
        await self._collection.insert_one(item.model_dump())
        return item

    async def insert_many(self, items: Iterable) -> None:
        await self._collection.insert_many((item.model_dump() for item in items))
