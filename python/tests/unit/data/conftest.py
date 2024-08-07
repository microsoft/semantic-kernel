# Copyright (c) Microsoft. All rights reserved.


from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Annotated, Any

import numpy as np
from pydantic import BaseModel, Field
from pytest import fixture

from semantic_kernel.data.vector_store_model_decorator import vectorstoremodel
from semantic_kernel.data.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_store_record_collection import VectorStoreRecordCollection
from semantic_kernel.data.vector_store_record_fields import (
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)


@fixture
def DictVectorStoreRecordCollection():
    class DictVectorStoreRecordCollection(VectorStoreRecordCollection[str, Any]):
        inner_storage: dict[str, Any] = Field(default_factory=dict)

        async def _inner_delete(self, keys: Sequence[str], **kwargs: Any) -> None:
            for key in keys:
                self.inner_storage.pop(key, None)

        async def _inner_get(self, keys: Sequence[str], **kwargs: Any) -> Any | Sequence[Any] | None:
            return [self.inner_storage[key] for key in keys if key in self.inner_storage]

        async def _inner_upsert(self, records: Sequence[Any], **kwargs: Any) -> Sequence[str]:
            updated_keys = []
            for record in records:
                key = (
                    record[self._key_field_name]
                    if isinstance(record, Mapping)
                    else getattr(record, self._key_field_name)
                )
                self.inner_storage[key] = record
                updated_keys.append(key)
            return updated_keys

        def _deserialize_store_models_to_dicts(self, records: Sequence[Any], **kwargs: Any) -> Sequence[dict[str, Any]]:
            return records

        def _serialize_dicts_to_store_models(self, records: Sequence[dict[str, Any]], **kwargs: Any) -> Sequence[Any]:
            return records

        async def create_collection(self, **kwargs: Any) -> None:
            pass

        async def delete_collection(self, **kwargs: Any) -> None:
            self.inner_storage = {}

        async def does_collection_exist(self, **kwargs: Any) -> bool:
            return True

    return DictVectorStoreRecordCollection


@fixture
def data_model_definition() -> object:
    return VectorStoreRecordDefinition(
        fields={
            "id": VectorStoreRecordKeyField(),
            "content": VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector"),
            "vector": VectorStoreRecordVectorField(),
        }
    )


@fixture
def data_model_serialize_definition() -> object:
    def serialize(record, **kwargs):
        return record

    def deserialize(records, **kwargs):
        return records

    return VectorStoreRecordDefinition(
        fields={
            "id": VectorStoreRecordKeyField(),
            "content": VectorStoreRecordDataField(),
            "vector": VectorStoreRecordVectorField(),
        },
        serialize=serialize,
        deserialize=deserialize,
    )


@fixture
def data_model_to_from_dict_definition() -> object:
    def to_dict(record, **kwargs):
        return record

    def from_dict(records, **kwargs):
        return records

    return VectorStoreRecordDefinition(
        fields={
            "id": VectorStoreRecordKeyField(),
            "content": VectorStoreRecordDataField(),
            "vector": VectorStoreRecordVectorField(),
        },
        to_dict=to_dict,
        from_dict=from_dict,
    )


@fixture
def data_model_container_definition() -> object:
    def to_dict(record: dict[str, dict[str, Any]], **kwargs) -> list[dict[str, Any]]:
        return [{"id": key} | value for key, value in record.items()]

    def from_dict(records: list[dict[str, Any]], **kwargs) -> dict[str, dict[str, Any]]:
        ret = {}
        for record in records:
            id = record.pop("id")
            ret[id] = record
        return ret

    return VectorStoreRecordDefinition(
        fields={
            "id": VectorStoreRecordKeyField(),
            "content": VectorStoreRecordDataField(),
            "vector": VectorStoreRecordVectorField(),
        },
        container_mode=True,
        to_dict=to_dict,
        from_dict=from_dict,
    )


@fixture
def data_model_container_serialize_definition() -> object:
    def serialize(record: dict[str, dict[str, Any]], **kwargs) -> list[dict[str, Any]]:
        return [{"id": key} | value for key, value in record.items()]

    def deserialize(records: list[dict[str, Any]], **kwargs) -> dict[str, dict[str, Any]]:
        ret = {}
        for record in records:
            id = record.pop("id")
            ret[id] = record
        return ret

    return VectorStoreRecordDefinition(
        fields={
            "id": VectorStoreRecordKeyField(),
            "content": VectorStoreRecordDataField(),
            "vector": VectorStoreRecordVectorField(),
        },
        container_mode=True,
        serialize=serialize,
        deserialize=deserialize,
    )


@fixture
def data_model_pandas_definition() -> object:
    from pandas import DataFrame

    return VectorStoreRecordDefinition(
        fields={
            "vector": VectorStoreRecordVectorField(
                name="vector",
                index_kind="hnsw",
                dimensions=5,
                distance_function="cosine",
                property_type="float",
            ),
            "id": VectorStoreRecordKeyField(name="id"),
            "content": VectorStoreRecordDataField(
                name="content",
                has_embedding=True,
                embedding_property_name="vector",
                property_type="str",
            ),
        },
        container_mode=True,
        to_dict=lambda x: x.to_dict(orient="records"),
        from_dict=lambda x, **_: DataFrame(x),
    )


@fixture
def data_model_type_vanilla():
    @vectorstoremodel
    class DataModelClass:
        def __init__(
            self,
            content: Annotated[str, VectorStoreRecordDataField()],
            vector: Annotated[list[float], VectorStoreRecordVectorField()],
            id: Annotated[str, VectorStoreRecordKeyField()],
        ):
            self.content = content
            self.vector = vector
            self.id = id

        def __eq__(self, other) -> bool:
            return self.content == other.content and self.id == other.id and self.vector == other.vector

    return DataModelClass


@fixture
def data_model_type_vector_array():
    @vectorstoremodel
    class DataModelClass:
        def __init__(
            self,
            content: Annotated[str, VectorStoreRecordDataField()],
            vector: Annotated[
                np.array,
                VectorStoreRecordVectorField(
                    serialize_function=np.ndarray.tolist,
                    deserialize_function=np.array,
                ),
            ],
            id: Annotated[str, VectorStoreRecordKeyField()],
        ):
            self.content = content
            self.vector = vector
            self.id = id

        def __eq__(self, other) -> bool:
            return self.content == other.content and self.id == other.id and self.vector == other.vector

    return DataModelClass


@fixture
def data_model_type_vanilla_serialize():
    @vectorstoremodel
    class DataModelClass:
        def __init__(
            self,
            content: Annotated[str, VectorStoreRecordDataField()],
            vector: Annotated[list[float], VectorStoreRecordVectorField()],
            id: Annotated[str, VectorStoreRecordKeyField()],
        ):
            self.content = content
            self.vector = vector
            self.id = id

        def serialize(self, **kwargs: Any) -> Any:
            """Serialize the object to the format required by the data store."""
            return {"id": self.id, "content": self.content, "vector": self.vector}

        @classmethod
        def deserialize(cls, obj: Any, **kwargs: Any):
            """Deserialize the output of the data store to an object."""
            return cls(**obj)

        def __eq__(self, other) -> bool:
            return self.content == other.content and self.id == other.id and self.vector == other.vector

    return DataModelClass


@fixture
def data_model_type_vanilla_to_from_dict():
    @vectorstoremodel
    class DataModelClass:
        def __init__(
            self,
            content: Annotated[str, VectorStoreRecordDataField()],
            vector: Annotated[list[float], VectorStoreRecordVectorField()],
            id: Annotated[str, VectorStoreRecordKeyField()],
        ):
            self.content = content
            self.vector = vector
            self.id = id

        def to_dict(self, **kwargs: Any) -> Any:
            """Serialize the object to the format required by the data store."""
            return {"id": self.id, "content": self.content, "vector": self.vector}

        @classmethod
        def from_dict(cls, *args: Any, **kwargs: Any):
            """Deserialize the output of the data store to an object."""
            return cls(**args[0])

        def __eq__(self, other) -> bool:
            return self.content == other.content and self.id == other.id and self.vector == other.vector

    return DataModelClass


@fixture
def data_model_type_pydantic():
    @vectorstoremodel
    class DataModelClass(BaseModel):
        content: Annotated[str, VectorStoreRecordDataField()]
        vector: Annotated[list[float], VectorStoreRecordVectorField()]
        id: Annotated[str, VectorStoreRecordKeyField()]

    return DataModelClass


@fixture
def data_model_type_dataclass():
    @vectorstoremodel
    @dataclass
    class DataModelClass:
        content: Annotated[str, VectorStoreRecordDataField()]
        vector: Annotated[list[float], VectorStoreRecordVectorField()]
        id: Annotated[str, VectorStoreRecordKeyField()]

    return DataModelClass
