# Copyright (c) Microsoft. All rights reserved.


from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Annotated, Any
from unittest.mock import AsyncMock, MagicMock

from pydantic import BaseModel, Field
from pytest import fixture, mark, raises

from semantic_kernel.data.vector_store_model_decorator import vectorstoremodel
from semantic_kernel.data.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_store_record_collection import VectorStoreRecordCollection
from semantic_kernel.data.vector_store_record_fields import (
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.exceptions.memory_connector_exceptions import MemoryConnectorException


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
            "content": VectorStoreRecordDataField(),
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
    # internal rep = {
    # "id1": {"content": "test_content", "vector": [1.0, 2.0, 3.0]},
    # "id2": {"content": "test_content", "vector": [1.0, 2.0, 3.0]}
    # }
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
        def deserialize(cls, obj: Any, **kwargs: Any) -> "DataModelClass":
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
        def from_dict(cls, *args: Any, **kwargs: Any) -> "DataModelClass":
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


@fixture(scope="function")
def vector_store_record_collection(
    DictVectorStoreRecordCollection,
    data_model_definition,
    data_model_serialize_definition,
    data_model_to_from_dict_definition,
    data_model_container_definition,
    data_model_container_serialize_definition,
    data_model_type_vanilla,
    data_model_type_vanilla_serialize,
    data_model_type_vanilla_to_from_dict,
    data_model_type_pydantic,
    data_model_type_dataclass,
    request,
) -> VectorStoreRecordCollection:
    idx = request.param if request and hasattr(request, "param") else 0

    defs = [
        data_model_definition,
        data_model_serialize_definition,
        data_model_to_from_dict_definition,
        data_model_container_definition,
        data_model_container_serialize_definition,
    ]
    if idx < len(defs):
        return DictVectorStoreRecordCollection(
            collection_name="test",
            data_model_type=dict,
            data_model_definition=defs[idx],
        )
    idx -= len(defs)
    types = [
        data_model_type_vanilla,
        data_model_type_vanilla_serialize,
        data_model_type_vanilla_to_from_dict,
        data_model_type_pydantic,
        data_model_type_dataclass,
    ]
    return DictVectorStoreRecordCollection(
        collection_name="test",
        data_model_type=types[idx],
    )


def test_init(DictVectorStoreRecordCollection, data_model_definition):
    vsrc = DictVectorStoreRecordCollection(
        collection_name="test",
        data_model_type=dict,
        data_model_definition=data_model_definition,
    )
    assert vsrc.collection_name == "test"
    assert vsrc.data_model_type is dict
    assert vsrc._container_mode is False
    assert vsrc.kernel is None
    assert vsrc.data_model_definition == data_model_definition
    assert vsrc._key_field_name == "id"


@mark.asyncio
@mark.parametrize(
    "vector_store_record_collection",
    [
        0,
        1,
        2,
        5,
        6,
        7,
        8,
        9,
    ],
    ids=[
        "none",
        "serialize",
        "to_from_dict",
        "vanilla_type",
        "vanilla_type_serialize",
        "vanilla_type_to_from_dict",
        "pydantic",
        "dataclass",
    ],
    indirect=True,
)
async def test_crud_operations(vector_store_record_collection):
    id = "test_id"
    record = {"id": id, "content": "test_content", "vector": [1.0, 2.0, 3.0]}
    if vector_store_record_collection.data_model_type is not dict:
        model = vector_store_record_collection.data_model_type
        record = model(**record)
    no_records = await vector_store_record_collection.get(id)
    assert no_records is None
    await vector_store_record_collection.upsert(record)
    assert len(vector_store_record_collection.inner_storage) == 1
    if vector_store_record_collection.data_model_type is dict:
        assert vector_store_record_collection.inner_storage[id] == record
    else:
        assert vector_store_record_collection.inner_storage[id]["content"] == record.content
    record_2 = await vector_store_record_collection.get(id)
    assert record_2 == record
    await vector_store_record_collection.delete(id)
    assert len(vector_store_record_collection.inner_storage) == 0


@mark.asyncio
async def test_upsert_fail(DictVectorStoreRecordCollection, data_model_definition):
    DictVectorStoreRecordCollection._inner_upsert = MagicMock(side_effect=Exception)
    vector_store_record_collection = DictVectorStoreRecordCollection(
        collection_name="test",
        data_model_type=dict,
        data_model_definition=data_model_definition,
    )
    record = {"id": "test_id", "content": "test_content", "vector": [1.0, 2.0, 3.0]}
    with raises(MemoryConnectorException, match="Error upserting record:"):
        await vector_store_record_collection.upsert(record)
    with raises(MemoryConnectorException, match="Error upserting records:"):
        await vector_store_record_collection.upsert_batch([record])
    assert len(vector_store_record_collection.inner_storage) == 0


@mark.asyncio
async def test_get_fail(DictVectorStoreRecordCollection, data_model_definition):
    DictVectorStoreRecordCollection._inner_get = MagicMock(side_effect=Exception)
    vector_store_record_collection = DictVectorStoreRecordCollection(
        collection_name="test",
        data_model_type=dict,
        data_model_definition=data_model_definition,
    )
    record = {"id": "test_id", "content": "test_content", "vector": [1.0, 2.0, 3.0]}
    await vector_store_record_collection.upsert(record)
    assert len(vector_store_record_collection.inner_storage) == 1
    with raises(MemoryConnectorException, match="Error getting record:"):
        await vector_store_record_collection.get("test_id")
    with raises(MemoryConnectorException, match="Error getting records:"):
        await vector_store_record_collection.get_batch(["test_id"])


@mark.asyncio
async def test_delete_fail(DictVectorStoreRecordCollection, data_model_definition):
    DictVectorStoreRecordCollection._inner_delete = MagicMock(side_effect=Exception)
    vector_store_record_collection = DictVectorStoreRecordCollection(
        collection_name="test",
        data_model_type=dict,
        data_model_definition=data_model_definition,
    )
    record = {"id": "test_id", "content": "test_content", "vector": [1.0, 2.0, 3.0]}
    await vector_store_record_collection.upsert(record)
    assert len(vector_store_record_collection.inner_storage) == 1
    with raises(MemoryConnectorException, match="Error deleting record:"):
        await vector_store_record_collection.delete("test_id")
    with raises(MemoryConnectorException, match="Error deleting records:"):
        await vector_store_record_collection.delete_batch(["test_id"])
    assert len(vector_store_record_collection.inner_storage) == 1


@mark.asyncio
@mark.parametrize(
    "vector_store_record_collection",
    [
        0,
        1,
        2,
        5,
        6,
        7,
        8,
        9,
    ],
    ids=[
        "none",
        "serialize",
        "to_from_dict",
        "vanilla_type",
        "vanilla_type_serialize",
        "vanilla_type_to_from_dict",
        "pydantic",
        "dataclass",
    ],
    indirect=True,
)
async def test_crud_batch_operations(vector_store_record_collection):
    ids = ["test_id_1", "test_id_2"]
    batch = [
        {"id": ids[0], "content": "test_content", "vector": [1.0, 2.0, 3.0]},
        {"id": ids[1], "content": "test_content", "vector": [1.0, 2.0, 3.0]},
    ]
    if vector_store_record_collection.data_model_type is not dict:
        model = vector_store_record_collection.data_model_type
        batch = [model(**record) for record in batch]
    no_records = await vector_store_record_collection.get_batch(ids)
    assert no_records is None
    await vector_store_record_collection.upsert_batch(batch)
    assert len(vector_store_record_collection.inner_storage) == 2
    if vector_store_record_collection.data_model_type is dict:
        assert vector_store_record_collection.inner_storage[ids[0]] == batch[0]
    else:
        assert vector_store_record_collection.inner_storage[ids[0]]["content"] == batch[0].content
    records = await vector_store_record_collection.get_batch(ids)
    assert records == batch
    await vector_store_record_collection.delete_batch(ids)
    assert len(vector_store_record_collection.inner_storage) == 0


@mark.asyncio
@mark.parametrize(
    "vector_store_record_collection",
    [3, 4],
    ids=["container", "container_serialize"],
    indirect=True,
)
async def test_crud_operations_container(vector_store_record_collection):
    id = "test_id"
    record = {id: {"content": "test_content", "vector": [1.0, 2.0, 3.0]}}
    no_records = await vector_store_record_collection.get(id)
    assert no_records is None
    await vector_store_record_collection.upsert(record)
    assert len(vector_store_record_collection.inner_storage) == 1
    assert vector_store_record_collection.inner_storage[id]["content"] == record[id]["content"]
    assert vector_store_record_collection.inner_storage[id]["vector"] == record[id]["vector"]
    record_2 = await vector_store_record_collection.get(id)
    assert record_2 == record
    await vector_store_record_collection.delete(id)
    assert len(vector_store_record_collection.inner_storage) == 0


@mark.asyncio
@mark.parametrize(
    "vector_store_record_collection",
    [3, 4],
    ids=["container", "container_serialize"],
    indirect=True,
)
async def test_crud_batch_operations_container(vector_store_record_collection):
    ids = ["test_id_1", "test_id_2"]
    batch = {
        ids[0]: {"content": "test_content", "vector": [1.0, 2.0, 3.0]},
        ids[1]: {"content": "test_content", "vector": [1.0, 2.0, 3.0]},
    }
    no_records = await vector_store_record_collection.get_batch(ids)
    assert no_records is None
    await vector_store_record_collection.upsert_batch(batch)
    assert len(vector_store_record_collection.inner_storage) == 2
    assert vector_store_record_collection.inner_storage[ids[0]]["content"] == batch[ids[0]]["content"]
    assert vector_store_record_collection.inner_storage[ids[0]]["vector"] == batch[ids[0]]["vector"]
    records = await vector_store_record_collection.get_batch(ids)
    assert records == batch
    await vector_store_record_collection.delete_batch(ids)
    assert len(vector_store_record_collection.inner_storage) == 0


@mark.asyncio
async def test_collection_operations(vector_store_record_collection):
    await vector_store_record_collection.create_collection()
    assert await vector_store_record_collection.does_collection_exist()
    record = {"id": "id", "content": "test_content", "vector": [1.0, 2.0, 3.0]}
    await vector_store_record_collection.upsert(record)
    assert len(vector_store_record_collection.inner_storage) == 1
    await vector_store_record_collection.delete_collection()
    assert vector_store_record_collection.inner_storage == {}
    await vector_store_record_collection.create_collection_if_not_exists()


@mark.asyncio
async def test_collection_create_if_not_exists(DictVectorStoreRecordCollection, data_model_definition):
    DictVectorStoreRecordCollection.does_collection_exist = AsyncMock(return_value=False)
    create_mock = AsyncMock()
    DictVectorStoreRecordCollection.create_collection = create_mock
    vector_store_record_collection = DictVectorStoreRecordCollection(
        collection_name="test",
        data_model_type=dict,
        data_model_definition=data_model_definition,
    )
    await vector_store_record_collection.create_collection_if_not_exists()
    create_mock.assert_called_once()


# TODO (eavanvalkenburg): exceptions during serialization, pydantic, to_dict
# TODO (eavanvalkenburg): vectorizing
# TODO (eavanvalkenburg): pandas container test
