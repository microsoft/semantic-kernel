# Copyright (c) Microsoft. All rights reserved.

import ast
from dataclasses import dataclass
from typing import Annotated

from pytest import fixture, mark
from qdrant_client.models import FieldCondition, Filter, MatchValue

from semantic_kernel.connectors.qdrant import QdrantCollection
from semantic_kernel.data.vector import VectorStoreField, vectorstoremodel


@vectorstoremodel
@dataclass
class TaggedRecord:
    id: Annotated[int, VectorStoreField("key")]
    opt_tag: Annotated[str | None, VectorStoreField("data")] = None
    vector: Annotated[list[float] | None, VectorStoreField("vector", dimensions=2)] = None


@fixture
async def tagged_collection():
    async with QdrantCollection(record_type=TaggedRecord, collection_name="test", location=":memory:") as collection:
        await collection.ensure_collection_exists()
        await collection.upsert([
            TaggedRecord(1, "red", [1.0, 0.2]),
            TaggedRecord(2, None, [0.0, 1.0]),
            TaggedRecord(3, "blue", [1.0, 1.0]),
        ])
        yield collection


def _field_conditions(filter_obj):
    if isinstance(filter_obj, FieldCondition):
        return [filter_obj]
    if isinstance(filter_obj, Filter):
        conditions = []
        for group in (filter_obj.must, filter_obj.should, filter_obj.must_not):
            if group:
                for item in group:
                    conditions.extend(_field_conditions(item))
        return conditions
    return []


@mark.parametrize(
    "filter_expr, expected_ids",
    [
        ("lambda x: x.opt_tag == None", [2]),
        ("lambda x: x.opt_tag != None", [1, 3]),
    ],
)
async def test_local_null_filter(tagged_collection, filter_expr, expected_ids):
    results = await tagged_collection.search(vector=[1.0, 1.0], filter=filter_expr)
    assert sorted([r.record.id async for r in results.results]) == expected_ids


@mark.parametrize(
    "filter_expr",
    ["lambda x: x.opt_tag == None", "lambda x: x.opt_tag != None"],
)
def test_lambda_parser_none_uses_is_null(filter_expr):
    collection = QdrantCollection(record_type=TaggedRecord, collection_name="test", location=":memory:")
    node = ast.parse(filter_expr, mode="eval").body.body
    parsed = collection._lambda_parser(node)

    conditions = _field_conditions(parsed)
    assert len(conditions) == 1
    assert conditions[0].key == "opt_tag"
    assert conditions[0].is_null is True
    assert conditions[0].match is None
    assert not any(isinstance(condition.match, MatchValue) for condition in conditions)
