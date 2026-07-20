import typing
from collections.abc import AsyncGenerator, Iterable, Sequence
from typing import Any

import pymongo.errors
from bson import ObjectId
from pymongo import UpdateOne
from pymongo.asynchronous.collection import AsyncCollection, ReturnDocument

from api.schemas.bases import MongoModel


class Repository[T: MongoModel]:
    def __init__(self, collection: AsyncCollection) -> None:
        self._collection = collection
        # noinspection PyUnresolvedReferences
        self._T = typing.get_args(self.__orig_bases__[0])[0]

    async def bulk_update(self, items: Sequence[T]) -> None:
        if not items:
            return

        await self._collection.bulk_write(
            [UpdateOne({'_id': item.mongo_id}, {'$set': item.model_dump(by_alias=True)}, upsert=True) for item in items]
        )

    async def delete(self, filter: dict[str, Any]) -> None:
        await self._collection.delete_many(filter)

    async def delete_by_id(self, id: str | ObjectId) -> None:
        await self.delete_one({'_id': id})

    async def delete_one(self, filter: dict[str, Any]) -> None:
        await self._collection.delete_one(filter)

    async def enforce_max_documents(
        self,
        max_documents: int,
        max_documents_sort_keys: Sequence[str | tuple[str, int]] | None = None
    ) -> None:
        if (excess := await self._collection.count_documents({}) - max_documents) <= 0:
            return

        cursor = self._collection.find(projection={'_id': True}, sort=max_documents_sort_keys, limit=excess)
        await self._collection.delete_many({'_id': {'$in': [document['_id'] async for document in cursor]}})

    async def get(
        self,
        filter: dict[str, Any] | None = None,
        sort_keys: Sequence[str | tuple[str, int]] | None = None,
        limit: int | None = None
    ) -> list[T]:
        return [object_ async for object_ in self.iter(filter, sort_keys, limit)]

    async def get_all(self, sort_keys: Sequence[str | tuple[str, int]] | None = None) -> list[T]:
        return await self.get(sort_keys=sort_keys)

    async def get_by_id(self, id: str | ObjectId) -> T | None:
        return await self.get_one({'_id': id})

    async def get_one(
        self,
        filter: dict[str, Any] | None = None,
        sort_keys: Sequence[str | tuple[str, int]] | None = None
    ) -> T | None:
        if document := await self._collection.find_one(filter, sort=sort_keys):
            return self._T(**document)

    async def insert(
        self,
        items: Iterable[T],
        max_documents: int | None = None,
        max_documents_sort_keys: Sequence[str | tuple[str, int]] | None = None
    ) -> None:
        try:
            await self._collection.insert_many((item.model_dump(by_alias=True) for item in items))
        except pymongo.errors.InvalidOperation:
            pass

        if max_documents is not None:
            await self.enforce_max_documents(max_documents, max_documents_sort_keys)

    async def insert_one(
        self,
        item: T,
        max_documents: int | None = None,
        max_documents_sort_keys: Sequence[str | tuple[str, int]] | None = None
    ) -> T:
        insert_result = await self._collection.insert_one(item.model_dump(by_alias=True))
        item.mongo_id = insert_result.inserted_id

        if max_documents is not None and await self._collection.count_documents({}) > max_documents:
            await self._collection.find_one_and_delete({}, sort=max_documents_sort_keys)

        return item

    async def iter(
        self,
        filter: dict[str, Any] | None = None,
        sort_keys: Sequence[str | tuple[str, int]] | None = None,
        limit: int | None = None
    ) -> AsyncGenerator[T]:
        async for document in self._collection.find(filter, sort=sort_keys, limit=limit if limit else 0):
            yield self._T(**document)

    async def iter_all(self, sort_keys: Sequence[str | tuple[str, int]] | None = None) -> AsyncGenerator[T]:
        async for object_ in self.iter(sort_keys=sort_keys):
            yield object_

    async def partial_update_one(
        self,
        filter: dict[str, Any],
        update: dict[str, Any],
        upsert: bool = False
    ) -> T | None:
        if document := await self._collection.find_one_and_update(
            filter,
            update,
            upsert=upsert,
            return_document=ReturnDocument.AFTER
        ):
            return self._T(**document)

    async def update_one(self, item: T, filter: dict[str, Any], upsert: bool = False) -> T | None:
        return await self.partial_update_one(filter, {'$set': item.model_dump(by_alias=True)}, upsert)

    async def update_one_by_id(self, item: T, upsert: bool = False) -> T | None:
        return await self.update_one(item, {'_id': item.mongo_id}, upsert)
