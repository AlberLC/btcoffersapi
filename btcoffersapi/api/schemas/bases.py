from typing import Annotated, Any

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, SerializerFunctionWrapHandler, model_serializer


class MongoModel[T](BaseModel):
    mongo_id: T | None = Field(alias='_id', default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ObjectIdModel(MongoModel[Annotated[ObjectId, PlainSerializer(str, when_used='json')]]):
    @model_serializer(mode='wrap')
    def serialize_model(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        data = handler(self)

        if not data['_id']:
            data.pop('_id')

        return data
