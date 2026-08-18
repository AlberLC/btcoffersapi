from typing import Annotated

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, PlainSerializer


class MongoModel[T](BaseModel):
    mongo_id: T = Field(alias='_id')

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ObjectIdModel(MongoModel[ObjectId]):
    mongo_id: Annotated[ObjectId, PlainSerializer(str, when_used='json')] = Field(alias='_id', default_factory=ObjectId)
