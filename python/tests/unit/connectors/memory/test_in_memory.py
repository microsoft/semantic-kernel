# Copyright (c) Microsoft. All rights reserved.

import ast

from pydantic import ConfigDict, Field, model_serializer  # 2026-10-05
from pytest import fixture, mark, raises

from semantic_kernel.connectors.in_memory import InMemoryCollection, InMemoryStore
from semantic_kernel.data._shared import default_dynamic_filter_function
from semantic_kernel.data.vector import DistanceFunction
from semantic_kernel.exceptions.vector_store_exceptions import VectorStoreOperationException


@fixture
def collection(definition):
    return InMemoryCollection(collection_name="test", record_type=dict, definition=definition)


def test_store_init():
    store = InMemoryStore()
    assert store is not None


def test_store_get_collection(definition):
    store = InMemoryStore()
    collection = store.get_collection(collection_name="test", record_type=dict, definition=definition)
    assert collection.collection_name == "test"
    assert collection.record_type is dict
    assert collection.definition == definition


async def test_upsert(collection):
    record = {"id": "testid", "content": "test content", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    key = await collection.upsert(record)
    assert key == "testid"
    assert collection.inner_storage == {"testid": record}


@mark.parametrize("batch", [False, True])
@mark.parametrize("model_kind", ["dict", "dataclass", "pydantic"])
async def test_upsert_with_key_storage_name(definition, dataclass_vector_data_model, record_type, batch, model_kind):
    definition.key_field.storage_name = "stored_id"
    model_type = {"dict": dict, "dataclass": dataclass_vector_data_model, "pydantic": record_type}[model_kind]
    collection = InMemoryCollection(collection_name="test", record_type=model_type, definition=definition)
    records = [
        model_type(id="first", content="first content", vector=[1.0, 0.0, 0.0, 0.0, 0.0]),
        model_type(id="second", content="second content", vector=[0.0, 1.0, 0.0, 0.0, 0.0]),
    ]

    keys = await collection.upsert(records if batch else records[0])
    assert keys == (["first", "second"] if batch else "first")
    assert await collection.get("first", include_vectors=True) == records[0]
    if batch:
        assert await collection.get(["first", "second"], include_vectors=True) == records

    results = await collection.search(vector=[1.0, 0.0, 0.0, 0.0, 0.0], include_vectors=True)
    found = [result.record async for result in results.results]
    assert found == (records if batch else records[:1])

    await collection.delete("first")
    assert await collection.get("first") is None
    if batch:
        assert await collection.get("second", include_vectors=True) == records[1]


@mark.parametrize("batch", [False, True])
async def test_upsert_when_storage_name_matches_logical_field(definition, record_type, batch):
    definition.key_field.storage_name = "content"
    collection = InMemoryCollection(collection_name="test", record_type=record_type, definition=definition)
    record = record_type(id="first", content="unrelated", vector=[1.0, 0.0, 0.0, 0.0, 0.0])

    keys = await collection.upsert([record] if batch else record)
    assert keys == (["first"] if batch else "first")
    assert "first" in collection.inner_storage
    assert "unrelated" not in collection.inner_storage

    await collection.delete("first")
    assert collection.inner_storage == {}


# 2026-10-05: 覆盖 Pydantic 逻辑字段与键存储名相撞时的单条和批量索引.
@mark.parametrize("batch", [False, True])
@mark.parametrize("serializer", ["default", "serialize_none", "model_serialize_none"])
async def test_upsert_when_key_storage_name_matches_another_logical_field(definition, record_type, batch, serializer):
    definition.key_field.storage_name = "content"
    if serializer == "serialize_none":
        definition.serialize = lambda record, **kwargs: None
    elif serializer == "model_serialize_none":

        class CustomRecord(record_type):
            def serialize(self, **kwargs):
                return None

        record_type = CustomRecord
    collection = InMemoryCollection(collection_name="test", record_type=record_type, definition=definition)
    records = [
        record_type(id="first", content="unrelated first", vector=[1.0, 0.0, 0.0, 0.0, 0.0]),
        record_type(id="second", content="unrelated second", vector=[0.0, 1.0, 0.0, 0.0, 0.0]),
    ]

    keys = await collection.upsert(records if batch else records[0])
    assert keys == (["first", "second"] if batch else "first")
    assert set(collection.inner_storage) == ({"first", "second"} if batch else {"first"})
    assert collection.inner_storage["first"] == records[0].model_dump()

    await collection.delete(["first", "second"] if batch else "first")
    assert collection.inner_storage == {}


# 2026-10-05: 覆盖其他字段的存储名与逻辑键相撞时的字典和 dataclass 序列化.
@mark.parametrize("batch", [False, True])
@mark.parametrize("model_kind", ["dict", "dataclass"])
async def test_upsert_when_another_storage_name_matches_key(definition, dataclass_vector_data_model, batch, model_kind):
    definition.key_field.storage_name = "stored_id"
    definition.fields[1].storage_name = "id"
    model_type = dict if model_kind == "dict" else dataclass_vector_data_model
    collection = InMemoryCollection(collection_name="test", record_type=model_type, definition=definition)
    records = [
        model_type(id="first", content="unrelated first", vector=[1.0, 0.0, 0.0, 0.0, 0.0]),
        model_type(id="second", content="unrelated second", vector=[0.0, 1.0, 0.0, 0.0, 0.0]),
    ]

    keys = await collection.upsert(records if batch else records[0])
    assert keys == (["first", "second"] if batch else "first")
    assert await collection.get("first", include_vectors=True) == records[0]
    if batch:
        assert await collection.get(["first", "second"], include_vectors=True) == records

    await collection.delete(["first", "second"] if batch else "first")
    assert collection.inner_storage == {}


# 2026-10-05: 自定义 Pydantic 序列化使用存储名时保留其实际键和值.
@mark.parametrize("batch", [False, True])
@mark.parametrize("serializer", ["to_dict", "serialize", "model_serialize", "model_dump", "model_serializer"])
async def test_upsert_with_pydantic_custom_storage_serialization(definition, record_type, batch, serializer):
    definition.key_field.storage_name = "stored_id"
    definition.fields[1].storage_name = "id"
    if serializer == "model_serialize":

        class CustomRecord(record_type):
            def serialize(self, **kwargs):
                return {"stored_id": self.id, "id": self.content, "vector": self.vector}

        model_type = CustomRecord
    elif serializer == "model_dump":

        class CustomDumpRecord(record_type):
            def model_dump(self, **kwargs):
                return {"stored_id": self.id, "id": self.content, "vector": self.vector}

        model_type = CustomDumpRecord
    elif serializer == "model_serializer":

        class CustomSerializedRecord(record_type):
            @model_serializer
            def serialize_model(self):
                return {"stored_id": self.id, "id": self.content, "vector": self.vector}

        model_type = CustomSerializedRecord
    else:
        model_type = record_type
        setattr(
            definition,
            serializer,
            lambda record, **kwargs: {"stored_id": record.id, "id": record.content, "vector": record.vector},
        )
    collection = InMemoryCollection(collection_name="test", record_type=model_type, definition=definition)
    records = [
        model_type(id="first", content="unrelated first", vector=[1.0, 0.0, 0.0, 0.0, 0.0]),
        model_type(id="second", content="unrelated second", vector=[0.0, 1.0, 0.0, 0.0, 0.0]),
    ]

    keys = await collection.upsert(records if batch else records[0])
    assert keys == (["first", "second"] if batch else "first")
    assert set(collection.inner_storage) == ({"first", "second"} if batch else {"first"})

    await collection.delete(["first", "second"] if batch else "first")
    assert collection.inner_storage == {}


# 2026-10-05: 默认按 Pydantic 序列化别名输出时使用实际键名, 避免反向别名碰撞.
@mark.parametrize("batch", [False, True])
async def test_upsert_with_pydantic_serialization_aliases(definition, record_type, batch):
    definition.key_field.storage_name = "stored_id"
    definition.fields[1].storage_name = "id"

    class AliasedRecord(record_type):
        model_config = ConfigDict(serialize_by_alias=True)
        id: str = Field(serialization_alias="stored_id")
        content: str = Field(serialization_alias="id")

    collection = InMemoryCollection(collection_name="test", record_type=AliasedRecord, definition=definition)
    records = [
        AliasedRecord(id="first", content="unrelated first", vector=[1.0, 0.0, 0.0, 0.0, 0.0]),
        AliasedRecord(id="second", content="unrelated second", vector=[0.0, 1.0, 0.0, 0.0, 0.0]),
    ]

    keys = await collection.upsert(records if batch else records[0])
    assert keys == (["first", "second"] if batch else "first")
    assert set(collection.inner_storage) == ({"first", "second"} if batch else {"first"})

    await collection.delete(["first", "second"] if batch else "first")
    assert collection.inner_storage == {}


async def test_get(collection):
    record = {"id": "testid", "content": "test content", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    await collection.upsert(record)
    result = await collection.get("testid")
    assert result["id"] == record["id"]
    assert result["content"] == record["content"]


async def test_get_missing(collection):
    result = await collection.get("testid")
    assert result is None


async def test_delete(collection):
    record = {"id": "testid", "content": "test content", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    await collection.upsert(record)
    await collection.delete("testid")
    assert collection.inner_storage == {}


async def test_collection_exists(collection):
    assert await collection.collection_exists() is True


async def test_ensure_collection_deleted(collection):
    record = {"id": "testid", "content": "test content", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    await collection.upsert(record)
    assert collection.inner_storage == {"testid": record}
    await collection.ensure_collection_deleted()
    assert collection.inner_storage == {}


async def test_ensure_collection_exists(collection):
    await collection.ensure_collection_exists()


@mark.parametrize(
    "distance_function",
    [
        DistanceFunction.COSINE_DISTANCE,
        DistanceFunction.COSINE_SIMILARITY,
        DistanceFunction.EUCLIDEAN_DISTANCE,
        DistanceFunction.MANHATTAN,
        DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE,
        DistanceFunction.DOT_PROD,
        DistanceFunction.HAMMING,
    ],
)
async def test_vectorized_search_similar(collection, distance_function):
    for field in collection.definition.fields:
        if field.name == "vector":
            field.distance_function = distance_function
    record1 = {"id": "testid1", "content": "test content", "vector": [1.0, 1.0, 1.0, 1.0, 1.0]}
    record2 = {"id": "testid2", "content": "test content", "vector": [-1.0, -1.0, -1.0, -1.0, -1.0]}
    await collection.upsert([record1, record2])
    results = await collection.search(
        vector=[0.9, 0.9, 0.9, 0.9, 0.9],
        vector_property_name="vector",
        include_total_count=True,
        include_vectors=True,
    )
    assert results.total_count == 2
    idx = 0
    async for res in results.results:
        assert res.record == record1 if idx == 0 else record2
        idx += 1


async def test_valid_lambda_filter(collection):
    record1 = {"id": "1", "vector": [1, 2, 3, 4, 5]}
    record2 = {"id": "2", "vector": [5, 4, 3, 2, 1]}
    await collection.upsert([record1, record2])
    # Filter to select only record with id == '1'
    results = collection._get_filtered_records(type("opt", (), {"filter": "lambda x: x.id == '1'"})())
    assert len(results) == 1
    assert "1" in results


async def test_valid_lambda_filter_attribute_access(collection):
    record1 = {"id": "1", "vector": [1, 2, 3, 4, 5]}
    record2 = {"id": "2", "vector": [5, 4, 3, 2, 1]}
    await collection.upsert([record1, record2])
    # Filter to select only record with id == '2' using attribute access
    results = collection._get_filtered_records(type("opt", (), {"filter": "lambda x: x['id'] == '2'"})())
    assert len(results) == 1
    assert "2" in results


async def test_invalid_filter_not_lambda(collection):
    with raises(VectorStoreOperationException, match="must be a lambda expression"):
        collection._get_filtered_records(type("opt", (), {"filter": "x.id == '1'"})())


async def test_invalid_filter_syntax(collection):
    with raises(VectorStoreOperationException, match="not valid Python"):
        collection._get_filtered_records(type("opt", (), {"filter": "lambda x: x.id == '1' and"})())


async def test_malicious_filter_import(collection):
    # Should not allow import statement
    with raises(VectorStoreOperationException):
        collection._get_filtered_records(
            type("opt", (), {"filter": "lambda x: __import__('os').system('echo malicious')"})()
        )


async def test_malicious_filter_exec(collection):
    # Should not allow exec or similar
    with raises(VectorStoreOperationException):
        collection._get_filtered_records(type("opt", (), {"filter": "lambda x: exec('print(1)')"})())


async def test_malicious_filter_builtins(collection):
    # Should not allow access to builtins
    with raises(VectorStoreOperationException):
        collection._get_filtered_records(
            type("opt", (), {"filter": "lambda x: __builtins__.__import__('os').system('echo malicious')"})()
        )


async def test_malicious_filter_open(collection):
    # Should not allow open()
    with raises(VectorStoreOperationException):
        collection._get_filtered_records(type("opt", (), {"filter": "lambda x: open('somefile.txt', 'w')"})())


async def test_malicious_filter_eval(collection):
    # Should not allow eval()
    with raises(VectorStoreOperationException):
        collection._get_filtered_records(type("opt", (), {"filter": "lambda x: eval('2+2')"})())


async def test_multiple_filters(collection):
    record1 = {"id": "1", "vector": [1, 2, 3, 4, 5]}
    record2 = {"id": "2", "vector": [5, 4, 3, 2, 1]}
    await collection.upsert([record1, record2])
    filters = ["lambda x: x.id == '1'", "lambda x: x.vector[0] == 1"]
    results = collection._get_filtered_records(type("opt", (), {"filter": filters})())
    assert len(results) == 1
    assert "1" in results


@mark.parametrize(
    "filter_str",
    [
        "lambda x: [x.clear][0]() or True",
        "lambda x: [x.update][0]({'role': 'admin'}) or True",
        "lambda x: [x.pop][0]('secret', '') or True",
        "lambda x: [x.__setitem__][0]('leaked', ['{0.__class__.__mro__}'.format][0](x)) or True",
    ],
)
def test_malicious_subscript_call_patterns_blocked(collection, filter_str):
    with raises(VectorStoreOperationException, match="Call target node type 'Subscript' is not allowed"):
        collection._parse_and_validate_filter(filter_str)


def test_direct_mutating_method_call_remains_blocked(collection):
    with raises(VectorStoreOperationException, match="Function 'clear' is not allowed"):
        collection._parse_and_validate_filter("lambda x: x.clear() or True")


@mark.parametrize(
    "attr",
    [
        "__base__",
        "__bases__",
        "__class__",
        "__mro__",
        "__subclasses__",
        "__globals__",
    ],
)
def test_blocked_dunder_attributes_rejected(collection, attr):
    with raises(VectorStoreOperationException, match=f"Access to attribute '{attr}' is not allowed"):
        collection._parse_and_validate_filter(f"lambda x: x.{attr}")


async def test_valid_lambda_filter_with_get_method(collection):
    record1 = {"id": "1", "vector": [1, 2, 3, 4, 5]}
    record2 = {"id": "2", "vector": [5, 4, 3, 2, 1]}
    await collection.upsert([record1, record2])
    results = collection._get_filtered_records(type("opt", (), {"filter": "lambda x: x.get('id') == '1'"})())
    assert len(results) == 1
    assert "1" in results


async def test_valid_lambda_filter_with_bounded_sequence_repeat(collection):
    record = {"id": "1", "vector": [1, 2, 3, 4, 5]}
    await collection.upsert(record)

    results = collection._get_filtered_records(type("opt", (), {"filter": "lambda x: ([0] * 2)[1] == 0"})())

    assert len(results) == 1
    assert "1" in results


async def test_sequence_repeat_limit_can_be_overridden(collection):
    record = {"id": "1", "vector": [1, 2, 3, 4, 5]}
    await collection.upsert(record)
    filter_options = type("opt", (), {"filter": "lambda x: ([0] * 2)[1] == 0"})()

    collection.max_filter_sequence_repeat_size = 1
    with raises(VectorStoreOperationException, match="Sequence repetition in filter expressions exceeds the maximum"):
        collection._get_filtered_records(filter_options)

    collection.max_filter_sequence_repeat_size = 2
    results = collection._get_filtered_records(filter_options)

    assert len(results) == 1
    assert "1" in results


async def test_callable_filter_cannot_mutate_stored_record(collection):
    record = {"id": "1", "content": "value", "vector": [1, 2, 3, 4, 5]}
    await collection.upsert(record)

    def mutating_filter(x):
        x["role"] = "admin"
        return True

    with raises(VectorStoreOperationException, match="Error running filter"):
        collection._get_filtered_records(type("opt", (), {"filter": mutating_filter})())

    assert "role" not in collection.inner_storage["1"]
    assert collection.inner_storage["1"]["content"] == "value"


def test_default_dynamic_filter_injection_payload_remains_string_literal(collection):
    class Param:
        def __init__(self, name, default_value=None):
            self.name = name
            self.default_value = default_value

    injected_value = "' or [x.update][0]({'role':'admin'}) or x.name=='"
    generated_filter = default_dynamic_filter_function(
        filter=None,
        parameters=[Param("category")],
        category=injected_value,
    )

    assert isinstance(generated_filter, str)
    tree = ast.parse(generated_filter, mode="eval")
    assert isinstance(tree.body, ast.Lambda)
    assert isinstance(tree.body.body, ast.Compare)
    assert isinstance(tree.body.body.comparators[0], ast.Constant)
    assert tree.body.body.comparators[0].value == injected_value

    filter_func = collection._parse_and_validate_filter(generated_filter)
    assert filter_func({"category": "finance", "name": "alice", "vector": [0.1] * 5}) is False


async def test_large_sequence_repeat_filter_is_blocked(collection):
    record = {"id": "1", "content": "value", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    await collection.upsert(record)

    with raises(VectorStoreOperationException, match="Sequence repetition in filter expressions exceeds the maximum"):
        collection._get_filtered_records(type("opt", (), {"filter": "lambda x: [0] * 2000000000"})())
