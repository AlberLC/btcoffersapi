import copy
import typing
from collections.abc import AsyncGenerator, Iterable, Sequence
from typing import Any, Self

import pymongo.errors
from bson import ObjectId
from pymongo import UpdateOne
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.collection import AsyncCollection, ReturnDocument

from api.schemas.bases import MongoModel


class Repository[T: MongoModel]:
    def __init__(self, collection: AsyncCollection, session: AsyncClientSession | None = None) -> None:
        self._collection = collection
        self._session = session
        # noinspection PyUnresolvedReferences
        self._T = typing.get_args(self.__orig_bases__[0])[0]

    async def bulk_update(self, items: Sequence[T], session: AsyncClientSession | None = None) -> None:
        if not items:
            return

        await self._collection.bulk_write(
            [
                UpdateOne({'_id': item.mongo_id}, {'$set': item.model_dump(by_alias=True)}, upsert=True)
                for item in items
            ],
            session=session or self._session
        )

    async def count(
        self,
        filter: dict[str, Any] | None = None,
        skip: int = 0,
        limit: int | None = None,
        session: AsyncClientSession | None = None
    ) -> int:
        kwargs = {}

        if limit is not None:
            kwargs['limit'] = limit

        return await self._collection.count_documents(
            filter or {},
            skip=skip,
            session=session or self._session,
            **kwargs
        )

    async def delete(self, filter: dict[str, Any], session: AsyncClientSession | None = None) -> None:
        await self._collection.delete_many(filter, session=session or self._session)

    async def delete_by_id(self, id: str | ObjectId, session: AsyncClientSession | None = None) -> None:
        await self.delete_one({'_id': id}, session)

    async def delete_one(self, filter: dict[str, Any], session: AsyncClientSession | None = None) -> None:
        await self._collection.delete_one(filter, session=session or self._session)

    async def enforce_max_documents(
        self,
        max_documents: int,
        max_documents_sort_keys: Sequence[str | tuple[str, int]] | None = None,
        session: AsyncClientSession | None = None
    ) -> None:
        if (excess := await self.count(session=session) - max_documents) <= 0:
            return

        session = session or self._session

        cursor = self._collection.find(
            projection={'_id': True},
            sort=max_documents_sort_keys,
            limit=excess,
            session=session
        )
        await self._collection.delete_many(
            {'_id': {'$in': [document['_id'] async for document in cursor]}},
            session=session
        )

    async def get(
        self,
        filter: dict[str, Any] | None = None,
        sort_keys: Sequence[str | tuple[str, int]] | None = None,
        skip: int = 0,
        limit: int | None = None,
        session: AsyncClientSession | None = None
    ) -> list[T]:
        return [object_ async for object_ in self.iter(filter, sort_keys, skip, limit, session)]

    async def get_by_id(self, id: str | ObjectId, session: AsyncClientSession | None = None) -> T | None:
        return await self.get_one({'_id': id}, session=session)

    async def get_one(
        self,
        filter: dict[str, Any] | None = None,
        sort_keys: Sequence[str | tuple[str, int]] | None = None,
        skip: int = 0,
        session: AsyncClientSession | None = None
    ) -> T | None:
        if document := await self._collection.find_one(
            filter,
            sort=sort_keys,
            skip=skip,
            session=session or self._session
        ):
            # noinspection not-mapping,unbound-local-variable
            return self._T(**document)

    async def insert(
        self,
        items: Iterable[T],
        max_documents: int | None = None,
        max_documents_sort_keys: Sequence[str | tuple[str, int]] | None = None,
        session: AsyncClientSession | None = None
    ) -> None:
        try:
            await self._collection.insert_many(
                (item.model_dump(by_alias=True) for item in items),
                session=session or self._session
            )
        except pymongo.errors.InvalidOperation:
            pass

        if max_documents is not None:
            await self.enforce_max_documents(max_documents, max_documents_sort_keys, session)

    async def insert_one(
        self,
        item: T,
        max_documents: int | None = None,
        max_documents_sort_keys: Sequence[str | tuple[str, int]] | None = None,
        session: AsyncClientSession | None = None
    ) -> None:
        session = session or self._session

        await self._collection.insert_one(item.model_dump(by_alias=True), session=session)

        if max_documents is not None and await self.count(session=session) > max_documents:
            await self._collection.find_one_and_delete({}, sort=max_documents_sort_keys, session=session)

    async def iter(
        self,
        filter: dict[str, Any] | None = None,
        sort_keys: Sequence[str | tuple[str, int]] | None = None,
        skip: int = 0,
        limit: int | None = None,
        session: AsyncClientSession | None = None
    ) -> AsyncGenerator[T]:
        kwargs = {}

        if limit is not None:
            kwargs['limit'] = limit

        cursor = self._collection.find(filter, sort=sort_keys, skip=skip, session=session or self._session, **kwargs)
        async for document in cursor:
            yield self._T(**document)

    async def partial_update_one(
        self,
        filter: dict[str, Any],
        update: dict[str, Any],
        upsert: bool = False,
        session: AsyncClientSession | None = None
    ) -> T | None:
        if document := await self._collection.find_one_and_update(
            filter,
            update,
            upsert=upsert,
            return_document=ReturnDocument.AFTER,
            session=session or self._session
        ):
            # noinspection not-mapping,unbound-local-variable
            return self._T(**document)

    async def update_by_id(self, item: T, upsert: bool = False, session: AsyncClientSession | None = None) -> T | None:
        return await self.update_one(item, {'_id': item.mongo_id}, upsert, session)

    async def update_one(
        self,
        item: T,
        filter: dict[str, Any],
        upsert: bool = False,
        session: AsyncClientSession | None = None
    ) -> T | None:
        return await self.partial_update_one(filter, {'$set': item.model_dump(by_alias=True)}, upsert, session)

    def with_session(self, session: AsyncClientSession | None = None) -> Self:
        repository = copy.copy(self)
        repository._session = session

        # noinspection bad-return
        return repository
