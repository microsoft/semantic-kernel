# Copyright (c) Microsoft. All rights reserved.

"""Regression: Vector store filters fail when constant is on the left or chained (#14779)."""

import ast
from unittest.mock import MagicMock

import pytest
from chromadb.api import ClientAPI
from qdrant_client.async_qdrant_client import AsyncQdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue, Range

from semantic_kernel.connectors.chroma import ChromaCollection
from semantic_kernel.connectors.in_memory import InMemoryCollection
from semantic_kernel.connectors.qdrant import QdrantCollection
from semantic_kernel.data.vector import (
    VectorStoreCollectionDefinition,
    VectorStoreField,
    _FoldUnaryNumericConstants,
    _NormalizeComparisonFilters,
)


@pytest.fixture
def numeric_definition() -> VectorStoreCollectionDefinition:
    return VectorStoreCollectionDefinition(
        fields=[
            VectorStoreField("key", name="id", type="str"),
            VectorStoreField("data", name="num", type="int"),
            VectorStoreField("data", name="status", type="str"),
            VectorStoreField("vector", name="vector", dimensions=2, type="float"),
        ]
    )


@pytest.mark.parametrize(
    "expression,expected_unparsed",
    [
        # Constant on left flipped to field on left
        ("lambda x: 2 < x.num", "lambda x: x.num > 2"),
        ("lambda x: 2 <= x.num", "lambda x: x.num >= 2"),
        ("lambda x: 2 > x.num", "lambda x: x.num < 2"),
        ("lambda x: 2 >= x.num", "lambda x: x.num <= 2"),
        ("lambda x: 3 == x.num", "lambda x: x.num == 3"),
        ("lambda x: 3 != x.num", "lambda x: x.num != 3"),
        ("lambda x: 'active' == x.status", "lambda x: x.status == 'active'"),
        ("lambda x: True == x.status", "lambda x: x.status == True"),
        ("lambda x: None == x.status", "lambda x: x.status == None"),
        ("lambda num: 2 < num", "lambda num: num > 2"),
        ("lambda num: 3 == num", "lambda num: num == 3"),
        # Field on left preserved as-is
        ("lambda x: x.num > 2", "lambda x: x.num > 2"),
        ("lambda x: x.num == 3", "lambda x: x.num == 3"),
        ("lambda x: x.status == 'active'", "lambda x: x.status == 'active'"),
        # Chained comparisons expanded and flipped
        ("lambda x: 1 <= x.num < 4", "lambda x: x.num >= 1 and x.num < 4"),
        ("lambda x: 1 < x.num < 10", "lambda x: x.num > 1 and x.num < 10"),
        ("lambda x: 4 > x.num >= 1", "lambda x: x.num < 4 and x.num >= 1"),
        ("lambda x: 10 >= x.num > 2", "lambda x: x.num <= 10 and x.num > 2"),
        # In / NotIn preserved
        ("lambda x: 2 in x.num", "lambda x: 2 in x.num"),
        ("lambda x: 'tag' not in x.status", "lambda x: 'tag' not in x.status"),
        # Two fields or two constants preserved
        ("lambda x: x.num < x.status", "lambda x: x.num < x.status"),
        ("lambda x: 1 < 2", "lambda x: 1 < 2"),
    ],
)
def test_normalize_comparison_filters_ast(expression, expected_unparsed):
    tree = ast.parse(expression)
    normalized = _NormalizeComparisonFilters().visit(tree)
    assert ast.unparse(normalized) == expected_unparsed


@pytest.mark.parametrize(
    "expression,expected_unparsed",
    [
        ("lambda x: -5 < x.num", "lambda x: x.num > -5"),
        ("lambda x: -5 <= x.num < 10", "lambda x: x.num >= -5 and x.num < 10"),
        ("lambda x: 10 >= x.num > -5", "lambda x: x.num <= 10 and x.num > -5"),
    ],
)
def test_normalize_comparison_filters_with_negative_literals(expression, expected_unparsed):
    tree = ast.parse(expression)
    folded = _FoldUnaryNumericConstants().visit(tree)
    normalized = _NormalizeComparisonFilters().visit(folded)
    assert ast.unparse(normalized) == expected_unparsed


def test_chroma_build_filter_constant_on_left(numeric_definition):
    collection = ChromaCollection(
        collection_name="test",
        record_type=dict,
        definition=numeric_definition,
        client=MagicMock(spec=ClientAPI),
    )
    assert collection._build_filter("lambda x: 2 < x.num") == {"num": {"$gt": 2}}
    assert collection._build_filter("lambda x: 3 == x.num") == {"num": 3}
    assert collection._build_filter("lambda x: 1 <= x.num < 4") == {"$and": [{"num": {"$gte": 1}}, {"num": {"$lt": 4}}]}
    assert collection._build_filter("lambda x: -5 < x.num") == {"num": {"$gt": -5}}


def test_qdrant_build_filter_constant_on_left(numeric_definition):
    collection = QdrantCollection(
        collection_name="test",
        record_type=dict,
        definition=numeric_definition,
        client=MagicMock(spec=AsyncQdrantClient),
    )
    assert collection._build_filter("lambda x: 2 < x.num") == FieldCondition(key="num", range=Range(gt=2.0))
    assert collection._build_filter("lambda x: 3 == x.num") == FieldCondition(key="num", match=MatchValue(value=3))
    assert collection._build_filter("lambda x: 1 <= x.num < 4") == Filter(
        must=[
            FieldCondition(key="num", range=Range(gte=1.0)),
            FieldCondition(key="num", range=Range(lt=4.0)),
        ]
    )
    assert collection._build_filter("lambda x: -5 < x.num") == FieldCondition(key="num", range=Range(gt=-5.0))


@pytest.mark.asyncio
async def test_in_memory_collection_searches_with_normalized_filters(numeric_definition):
    collection = InMemoryCollection(
        collection_name="test",
        record_type=dict,
        definition=numeric_definition,
    )
    records = [{"id": f"rec_{i}", "num": i, "status": "active", "vector": [1.0, 0.0]} for i in range(6)]
    await collection.upsert(records)

    # lambda x: 2 < x.num -> expected records 3, 4, 5
    res = await collection.search(vector=[1.0, 0.0], filter="lambda x: 2 < x.num", top=10)
    hits = [hit.record["num"] async for hit in res.results]
    assert sorted(hits) == [3, 4, 5]

    # lambda x: 3 == x.num -> expected record 3
    res = await collection.search(vector=[1.0, 0.0], filter="lambda x: 3 == x.num", top=10)
    hits = [hit.record["num"] async for hit in res.results]
    assert hits == [3]

    # lambda x: 1 <= x.num < 4 -> expected records 1, 2, 3
    res = await collection.search(vector=[1.0, 0.0], filter="lambda x: 1 <= x.num < 4", top=10)
    hits = [hit.record["num"] async for hit in res.results]
    assert sorted(hits) == [1, 2, 3]
