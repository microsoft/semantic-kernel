# Copyright (c) Microsoft. All rights reserved.

from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock, Mock, PropertyMock, patch

from pandas import DataFrame
from pytest import mark, raises

from semantic_kernel.data.definitions import SerializeMethodProtocol, ToDictMethodProtocol
from semantic_kernel.exceptions import (
    VectorStoreModelDeserializationException,
    VectorStoreModelSerializationException,
    VectorStoreModelValidationError,
    VectorStoreOperationException,
)


# region init
def test_init(DictVectorStoreRecordCollection, definition):
    vsrc = DictVectorStoreRecordCollection(
        collection_name="test",
        record_type=dict,
        definition=definition,
    )
    assert vsrc.collection_name == "test"
    assert vsrc.record_type is dict
    assert vsrc._container_mode is False
    assert vsrc.definition == definition
    assert vsrc._key_field_name == "id"


def test_data_model_validation(record_type_vanilla, DictVectorStoreRecordCollection):
    DictVectorStoreRecordCollection.supported_key_types = PropertyMock(return_value=["str"])
    DictVectorStoreRecordCollection.supported_vector_types = PropertyMock(return_value=["float"])
    DictVectorStoreRecordCollection(
        collection_name="test",
        record_type=record_type_vanilla,
    )


def test_data_model_validation_key_fail(record_type_vanilla, DictVectorStoreRecordCollection):
    DictVectorStoreRecordCollection.supported_key_types = PropertyMock(return_value=["int"])
    with raises(VectorStoreModelValidationError, match="Key field must be one of"):
        DictVectorStoreRecordCollection(
            collection_name="test",
            record_type=record_type_vanilla,
        )


def test_data_model_validation_vector_fail(record_type_vanilla, DictVectorStoreRecordCollection):
    DictVectorStoreRecordCollection.supported_vector_types = PropertyMock(return_value={"list[int]"})
    with raises(VectorStoreModelValidationError):
        DictVectorStoreRecordCollection(
            collection_name="test",
            record_type=record_type_vanilla,
        )


# region Collection
async def test_collection_operations(vector_store_record_collection):
    await vector_store_record_collection.create_collection()
    assert await vector_store_record_collection.does_collection_exist()
    record = {"id": "id", "content": "test_content", "vector": [1.0, 2.0, 3.0]}
    await vector_store_record_collection.upsert(record)
    assert len(vector_store_record_collection.inner_storage) == 1
    await vector_store_record_collection.ensure_collection_deleted()
    assert vector_store_record_collection.inner_storage == {}
    await vector_store_record_collection.ensure_collection_exists()


async def test_collection_create_if_not_exists(DictVectorStoreRecordCollection, definition):
    DictVectorStoreRecordCollection.does_collection_exist = AsyncMock(return_value=False)
    create_mock = AsyncMock()
    DictVectorStoreRecordCollection.create_collection = create_mock
    vector_store_record_collection = DictVectorStoreRecordCollection(
        collection_name="test",
        record_type=dict,
        definition=definition,
    )
    await vector_store_record_collection.ensure_collection_exists()
    create_mock.assert_called_once()


# region CRUD


@mark.parametrize(
    "vector_store_record_collection",
    [
        "definition_basic",
        "definition_with_serialize",
        "definition_with_to_from",
        "type_vanilla",
        "type_vanilla_with_serialize",
        "type_vanilla_with_to_from_dict",
        "type_pydantic",
        "type_dataclass",
    ],
    indirect=True,
)
async def test_crud_operations(vector_store_record_collection):
    ids = ["test_id_1", "test_id_2"]
    batch = [
        {"id": ids[0], "content": "test_content", "vector": [1.0, 2.0, 3.0]},
        {"id": ids[1], "content": "test_content", "vector": [1.0, 2.0, 3.0]},
    ]
    if vector_store_record_collection.record_type is not dict:
        model = vector_store_record_collection.record_type
        batch = [model(**record) for record in batch]
    no_records = await vector_store_record_collection.get(ids)
    assert no_records is None
    await vector_store_record_collection.upsert(batch)
    assert len(vector_store_record_collection.inner_storage) == 2
    if vector_store_record_collection.record_type is dict:
        assert vector_store_record_collection.inner_storage[ids[0]] == batch[0]
    else:
        assert not isinstance(batch[0], dict)
        assert vector_store_record_collection.inner_storage[ids[0]]["content"] == batch[0].content
    records = await vector_store_record_collection.get(ids, include_vector=True)
    for idx, rec in enumerate(records):
        if vector_store_record_collection.record_type is dict:
            assert rec["id"] == batch[idx]["id"]
            assert rec["content"] == batch[idx]["content"]
        else:
            assert rec.id == batch[idx].id
            assert rec.content == batch[idx].content
    await vector_store_record_collection.delete(ids)
    assert len(vector_store_record_collection.inner_storage) == 0


@mark.parametrize(
    "vector_store_record_collection",
    ["definition_container", "definition_container_serialize"],
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
    record_2["id"] = id
    record_2["content"] = record_2[id]["content"]
    await vector_store_record_collection.delete(id)
    assert len(vector_store_record_collection.inner_storage) == 0


@mark.parametrize(
    "vector_store_record_collection",
    ["definition_container", "definition_container_serialize"],
    indirect=True,
)
async def test_crud_batch_operations_container(vector_store_record_collection):
    ids = ["test_id_1", "test_id_2"]
    batch = {
        ids[0]: {"content": "test_content", "vector": [1.0, 2.0, 3.0]},
        ids[1]: {"content": "test_content", "vector": [1.0, 2.0, 3.0]},
    }
    no_records = await vector_store_record_collection.get(ids)
    assert no_records is None
    await vector_store_record_collection.upsert(batch)
    assert len(vector_store_record_collection.inner_storage) == 2
    assert vector_store_record_collection.inner_storage[ids[0]]["content"] == batch[ids[0]]["content"]
    assert vector_store_record_collection.inner_storage[ids[0]]["vector"] == batch[ids[0]]["vector"]
    records = await vector_store_record_collection.get(ids)
    assert records == batch
    await vector_store_record_collection.delete(ids)
    assert len(vector_store_record_collection.inner_storage) == 0


@mark.parametrize(
    "vector_store_record_collection",
    ["definition_pandas"],
    indirect=True,
)
async def test_crud_operations_pandas(vector_store_record_collection):
    id = "test_id"
    record = DataFrame([{"id": id, "content": "test_content", "vector": [1.0, 2.0, 3.0]}])
    no_records = await vector_store_record_collection.get(id)
    assert no_records is None
    await vector_store_record_collection.upsert(record)
    assert len(vector_store_record_collection.inner_storage) == 1

    assert vector_store_record_collection.inner_storage[id]["content"] == record["content"].values[0]
    assert vector_store_record_collection.inner_storage[id]["vector"] == record["vector"].values[0]
    record_2 = await vector_store_record_collection.get(id)
    assert record_2.equals(record)
    await vector_store_record_collection.delete(id)
    assert len(vector_store_record_collection.inner_storage) == 0


@mark.parametrize(
    "vector_store_record_collection",
    ["definition_pandas"],
    indirect=True,
)
async def test_crud_batch_operations_pandas(vector_store_record_collection):
    ids = ["test_id_1", "test_id_2"]

    batch = DataFrame([{"id": id, "content": "test_content", "vector": [1.0, 2.0, 3.0]} for id in ids])
    no_records = await vector_store_record_collection.get(ids)
    assert no_records is None
    await vector_store_record_collection.upsert(batch)
    assert len(vector_store_record_collection.inner_storage) == 2
    assert vector_store_record_collection.inner_storage[ids[0]]["content"] == batch["content"].values[0]
    assert vector_store_record_collection.inner_storage[ids[0]]["vector"] == batch["vector"].values[0]
    records = await vector_store_record_collection.get(ids)
    assert records.equals(batch)
    await vector_store_record_collection.delete(ids)
    assert len(vector_store_record_collection.inner_storage) == 0


# region Fails
async def test_upsert_fail(DictVectorStoreRecordCollection, definition):
    DictVectorStoreRecordCollection._inner_upsert = MagicMock(side_effect=Exception)
    vector_store_record_collection = DictVectorStoreRecordCollection(
        collection_name="test",
        record_type=dict,
        definition=definition,
    )
    record = {"id": "test_id", "content": "test_content", "vector": [1.0, 2.0, 3.0]}
    with raises(VectorStoreOperationException, match="Error upserting record"):
        await vector_store_record_collection.upsert(record)
    with raises(VectorStoreOperationException, match="Error upserting record"):
        await vector_store_record_collection.upsert([record])
    with raises(VectorStoreOperationException, match="Error upserting record"):
        await vector_store_record_collection.upsert([record])
    assert len(vector_store_record_collection.inner_storage) == 0


async def test_get_fail(DictVectorStoreRecordCollection, definition):
    DictVectorStoreRecordCollection._inner_get = MagicMock(side_effect=Exception)
    vector_store_record_collection = DictVectorStoreRecordCollection(
        collection_name="test",
        record_type=dict,
        definition=definition,
    )
    record = {"id": "test_id", "content": "test_content", "vector": [1.0, 2.0, 3.0]}
    await vector_store_record_collection.upsert(record)
    assert len(vector_store_record_collection.inner_storage) == 1
    with raises(VectorStoreOperationException, match="Error getting record"):
        await vector_store_record_collection.get("test_id")
    with raises(VectorStoreOperationException, match="Error getting record"):
        await vector_store_record_collection.get(["test_id"])
    with raises(VectorStoreOperationException, match="Error getting record"):
        await vector_store_record_collection.get(["test_id"])


async def test_deserialize_in_get_fail(DictVectorStoreRecordCollection, definition):
    definition.deserialize = MagicMock(side_effect=Exception)
    vector_store_record_collection = DictVectorStoreRecordCollection(
        collection_name="test",
        record_type=dict,
        definition=definition,
    )
    record = {"id": "test_id", "content": "test_content", "vector": [1.0, 2.0, 3.0]}
    await vector_store_record_collection.upsert(record)
    assert len(vector_store_record_collection.inner_storage) == 1
    with raises(VectorStoreModelDeserializationException, match="Error deserializing records:"):
        await vector_store_record_collection.get("test_id")
    with raises(VectorStoreModelDeserializationException, match="Error deserializing records:"):
        await vector_store_record_collection.get(["test_id"])


async def test_get_fail_multiple(DictVectorStoreRecordCollection, definition):
    vector_store_record_collection = DictVectorStoreRecordCollection(
        collection_name="test",
        record_type=dict,
        definition=definition,
    )
    record = {"id": "test_id", "content": "test_content", "vector": [1.0, 2.0, 3.0]}
    await vector_store_record_collection.upsert(record)
    assert len(vector_store_record_collection.inner_storage) == 1
    with (
        patch("semantic_kernel.data.vectors.VectorStoreRecordCollection.deserialize") as deserialize_mock,
        raises(
            VectorStoreModelDeserializationException, match="Error deserializing record, multiple records returned:"
        ),
    ):
        deserialize_mock.return_value = [
            {"id": "test_id", "content": "test_content", "vector": [1.0, 2.0, 3.0]},
            {"id": "test_id", "content": "test_content", "vector": [1.0, 2.0, 3.0]},
        ]
        await vector_store_record_collection.get("test_id")


async def test_delete_fail(DictVectorStoreRecordCollection, definition):
    DictVectorStoreRecordCollection._inner_delete = MagicMock(side_effect=Exception)
    vector_store_record_collection = DictVectorStoreRecordCollection(
        collection_name="test",
        record_type=dict,
        definition=definition,
    )
    record = {"id": "test_id", "content": "test_content", "vector": [1.0, 2.0, 3.0]}
    await vector_store_record_collection.upsert(record)
    assert len(vector_store_record_collection.inner_storage) == 1
    with raises(VectorStoreOperationException, match="Error deleting record"):
        await vector_store_record_collection.delete("test_id")
    with raises(VectorStoreOperationException, match="Error deleting record"):
        await vector_store_record_collection.delete(["test_id"])
    with raises(VectorStoreOperationException, match="Error deleting record"):
        await vector_store_record_collection.delete(["test_id"])
    assert len(vector_store_record_collection.inner_storage) == 1


# region Serialize
async def test_serialize_in_upsert_fail(DictVectorStoreRecordCollection, definition):
    DictVectorStoreRecordCollection.serialize = MagicMock(side_effect=VectorStoreModelSerializationException)
    vector_store_record_collection = DictVectorStoreRecordCollection(
        collection_name="test",
        record_type=dict,
        definition=definition,
    )
    record = {"id": "test_id", "content": "test_content", "vector": [1.0, 2.0, 3.0]}
    with raises(VectorStoreModelSerializationException):
        await vector_store_record_collection.upsert(record)
    with raises(VectorStoreModelSerializationException):
        await vector_store_record_collection.upsert([record])


async def test_serialize_record_type_serialize_fail(DictVectorStoreRecordCollection, record_type_vanilla_serialize):
    vector_store_record_collection = DictVectorStoreRecordCollection(
        collection_name="test",
        record_type=record_type_vanilla_serialize,
    )
    record = MagicMock(spec=SerializeMethodProtocol)
    record.serialize = MagicMock(side_effect=Exception)
    with raises(VectorStoreModelSerializationException, match="Error serializing record"):
        await vector_store_record_collection.serialize(record)


def test_serialize_data_model_to_dict_fail_object(DictVectorStoreRecordCollection, record_type_vanilla):
    vector_store_record_collection = DictVectorStoreRecordCollection(
        collection_name="test",
        record_type=record_type_vanilla,
    )
    record = Mock(spec=record_type_vanilla)
    with raises(AttributeError):
        vector_store_record_collection._serialize_data_model_to_dict(record)


@mark.parametrize("vector_store_record_collection", ["type_pydantic"], indirect=True)
async def test_pydantic_serialize_fail(vector_store_record_collection):
    id = "test_id"
    model = deepcopy(vector_store_record_collection.record_type)
    model.model_dump = MagicMock(side_effect=Exception)
    vector_store_record_collection.record_type = model
    dict_record = {"id": id, "content": "test_content", "vector": [1.0, 2.0, 3.0]}
    record = model(**dict_record)
    with raises(VectorStoreModelSerializationException, match="Error serializing record"):
        await vector_store_record_collection.serialize(record)


@mark.parametrize("vector_store_record_collection", ["type_vanilla_with_to_from_dict"], indirect=True)
async def test_to_dict_fail(vector_store_record_collection):
    record = MagicMock(spec=ToDictMethodProtocol)
    record.to_dict = MagicMock(side_effect=Exception)
    with raises(VectorStoreModelSerializationException, match="Error serializing record"):
        await vector_store_record_collection.serialize(record)


# region Deserialize


async def test_deserialize_definition_fail(DictVectorStoreRecordCollection, definition):
    definition.deserialize = MagicMock(side_effect=Exception)
    vector_store_record_collection = DictVectorStoreRecordCollection(
        collection_name="test",
        record_type=dict,
        definition=definition,
    )
    record = {"id": "test_id", "content": "test_content", "vector": [1.0, 2.0, 3.0]}
    vector_store_record_collection.inner_storage["test_id"] = record
    with raises(VectorStoreModelDeserializationException, match="Error deserializing record"):
        await vector_store_record_collection.get("test_id")
    with raises(VectorStoreModelDeserializationException, match="Error deserializing record"):
        await vector_store_record_collection.get(["test_id"])


async def test_deserialize_definition_none(DictVectorStoreRecordCollection, definition):
    vector_store_record_collection = DictVectorStoreRecordCollection(
        collection_name="test",
        record_type=dict,
        definition=definition,
    )
    assert vector_store_record_collection.deserialize([]) is None
    assert vector_store_record_collection.deserialize({}) is None


def test_deserialize_type_fail(DictVectorStoreRecordCollection, record_type_vanilla_serialize):
    vector_store_record_collection = DictVectorStoreRecordCollection(
        collection_name="test",
        record_type=record_type_vanilla_serialize,
    )
    record = {"id": "test_id", "content": "test_content", "vector": [1.0, 2.0, 3.0]}
    vector_store_record_collection.record_type.deserialize = MagicMock(side_effect=Exception)
    with raises(VectorStoreModelDeserializationException, match="Error deserializing record"):
        vector_store_record_collection.deserialize(record)


def test_deserialize_dict_data_model_fail_sequence(DictVectorStoreRecordCollection, record_type_vanilla):
    vector_store_record_collection = DictVectorStoreRecordCollection(
        collection_name="test",
        record_type=record_type_vanilla,
    )
    with raises(VectorStoreModelDeserializationException, match="Cannot deserialize multiple records"):
        vector_store_record_collection._deserialize_dict_to_data_model([{}, {}])


def test_deserialize_dict_data_model_shortcut(DictVectorStoreRecordCollection, definition):
    vector_store_record_collection = DictVectorStoreRecordCollection(
        collection_name="test",
        record_type=dict,
        definition=definition,
    )
    record = vector_store_record_collection._deserialize_dict_to_data_model([
        {"id": "test_id", "content": "test_content", "vector": [1.0, 2.0, 3.0]}
    ])
    assert record == {"id": "test_id", "content": "test_content"}


@mark.parametrize("vector_store_record_collection", ["type_pydantic"], indirect=True)
async def test_pydantic_deserialize_fail(vector_store_record_collection):
    id = "test_id"
    dict_record = {"id": id, "content": "test_content", "vector": [1.0, 2.0, 3.0]}
    vector_store_record_collection.record_type.model_validate = MagicMock(side_effect=Exception)
    with raises(VectorStoreModelDeserializationException, match="Error deserializing record"):
        vector_store_record_collection.deserialize(dict_record)


@mark.parametrize("vector_store_record_collection", ["type_vanilla_with_to_from_dict"], indirect=True)
def test_from_dict_fail(vector_store_record_collection):
    id = "test_id"
    model = deepcopy(vector_store_record_collection.record_type)
    dict_record = {"id": id, "content": "test_content", "vector": [1.0, 2.0, 3.0]}
    model.from_dict = MagicMock(side_effect=Exception)
    vector_store_record_collection.record_type = model
    with raises(VectorStoreModelDeserializationException, match="Error deserializing record"):
        vector_store_record_collection.deserialize(dict_record)
