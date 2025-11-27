import typing
from collections.abc import Iterable

from bson import ObjectId
from pydantic import BaseModel
from pymongo.asynchronous.collection import AsyncCollection

from database.client import create_object_id
from database.locks import database_lock


class Repository[T: BaseModel]:
    def __init__(self, collection: AsyncCollection) -> None:
        self._collection = collection
        self._T = typing.get_args(self.__orig_bases__[0])[0]

    async def delete(self, id: str) -> None:
        await self._collection.delete_one({'id': id})

    async def delete_many(self, filter: dict) -> None:
        await self._collection.delete_many(filter)

    async def get_all(self, sort_keys: str | Iterable[str | tuple[str, int]] = ()) -> list[T]:
        async with database_lock():
            cursor = self._collection.find()

            if sort_keys:
                cursor.sort(sort_keys)

            return [self._T(**document) async for document in cursor]

    async def get_by_object_id(self, object_id: str | ObjectId) -> T | None:
        if isinstance(object_id, str):
            object_id = create_object_id(object_id)

        async with database_lock():
            if document := await self._collection.find_one({'_id': object_id}):
                return self._T(**document)

    async def insert(self, item: T) -> T:
        await self._collection.insert_one(item.model_dump())
        return item

    async def insert_many(self, items: Iterable[T]) -> None:
        await self._collection.insert_many((item.model_dump() for item in items))
