# Copyright (c) Microsoft. All rights reserved.

"""Unit and integration tests for comparison normalization in vector store filter lambdas."""

import ast
from ast import Attribute, BoolOp, Compare, Constant, Eq, Gt, GtE, Lt, LtE, Name, NotEq, parse
from unittest.mock import AsyncMock, MagicMock

import pytest
from chromadb.api import ClientAPI
from qdrant_client.async_qdrant_client import AsyncQdrantClient
from qdrant_client.models import FieldCondition, Range
from qdrant_client.models import Filter as QdrantFilter
from weaviate import WeaviateAsyncClient
from weaviate.classes.query import Filter as WeaviateFilter

from semantic_kernel.connectors.chroma import ChromaCollection
from semantic_kernel.connectors.qdrant import QdrantCollection
from semantic_kernel.connectors.weaviate import WeaviateCollection
from semantic_kernel.data.vector import (
    VectorStoreCollectionDefinition,
    VectorStoreField,
    _FoldUnaryNumericConstants,
    _NormalizeComparisonConstants,
)


@pytest.fixture
def numeric_definition() -> VectorStoreCollectionDefinition:
    return VectorStoreCollectionDefinition(
        fields=[
            VectorStoreField("key", name="id", type="str"),
            VectorStoreField("data", name="price", type="float"),
            VectorStoreField("data", name="temperature", type="float"),
            VectorStoreField("vector", name="vector", dimensions=2, type="float"),
        ]
    )


@pytest.mark.parametrize(
    "expr_str,expected_op,expected_constant",
    [
        ("lambda x: 5 < x.price", Gt, 5),
        ("lambda x: 5 <= x.price", GtE, 5),
        ("lambda x: 5 > x.price", Lt, 5),
        ("lambda x: 5 >= x.price", LtE, 5),
        ('lambda x: "active" == x.status', Eq, "active"),
        ("lambda x: 10 != x.id", NotEq, 10),
    ],
)
def test_normalize_single_comparison_flips_constant_on_left(expr_str, expected_op, expected_constant):
    tree = parse(expr_str)
    transformed = _NormalizeComparisonConstants().visit(tree)
    compare = transformed.body[0].value.body

    assert isinstance(compare, Compare)
    assert len(compare.ops) == 1
    assert isinstance(compare.ops[0], expected_op)
    assert isinstance(compare.left, Attribute)
    assert isinstance(compare.comparators[0], Constant)
    assert compare.comparators[0].value == expected_constant


def test_normalize_single_comparison_works_with_bare_name():
    tree = parse("lambda price: 5 > price")
    transformed = _NormalizeComparisonConstants().visit(tree)
    compare = transformed.body[0].value.body

    assert isinstance(compare, Compare)
    assert isinstance(compare.ops[0], Lt)
    assert isinstance(compare.left, Name)
    assert compare.left.id == "price"
    assert isinstance(compare.comparators[0], Constant)
    assert compare.comparators[0].value == 5


def test_normalize_folded_negative_constant_on_left():
    tree = parse("lambda x: -5 > x.price")
    tree = _FoldUnaryNumericConstants().visit(tree)
    transformed = _NormalizeComparisonConstants().visit(tree)
    compare = transformed.body[0].value.body

    assert isinstance(compare, Compare)
    assert isinstance(compare.ops[0], Lt)
    assert isinstance(compare.left, Attribute)
    assert isinstance(compare.comparators[0], Constant)
    assert compare.comparators[0].value == -5


@pytest.mark.parametrize(
    "expr_str",
    [
        "lambda x: x.price > 5",
        "lambda x: x.price <= 5",
        'lambda x: x.status == "active"',
        "lambda x: x.id != 10",
    ],
)
def test_normalize_preserves_constant_on_right(expr_str):
    tree = parse(expr_str)
    original_dump = ast.dump(tree)
    transformed = _NormalizeComparisonConstants().visit(tree)
    assert ast.dump(transformed) == original_dump


@pytest.mark.parametrize(
    "expr_str",
    [
        'lambda x: x.tag in ["a", "b"]',
        'lambda x: "a" in x.tags',
        "lambda x: x.price == x.discount",
        "lambda x: 5 == 5",
    ],
)
def test_normalize_preserves_non_invertible_comparisons(expr_str):
    tree = parse(expr_str)
    original_dump = ast.dump(tree)
    transformed = _NormalizeComparisonConstants().visit(tree)
    assert ast.dump(transformed) == original_dump


def test_normalize_chained_comparisons_decomposes_into_and():
    tree = parse("lambda x: 0 <= x.price < 5")
    transformed = _NormalizeComparisonConstants().visit(tree)
    body = transformed.body[0].value.body

    assert isinstance(body, BoolOp)
    assert isinstance(body.op, ast.And)
    assert len(body.values) == 2

    first = body.values[0]
    assert isinstance(first, Compare)
    assert isinstance(first.ops[0], GtE)
    assert isinstance(first.left, Attribute)
    assert first.left.attr == "price"
    assert isinstance(first.comparators[0], Constant)
    assert first.comparators[0].value == 0

    second = body.values[1]
    assert isinstance(second, Compare)
    assert isinstance(second.ops[0], Lt)
    assert isinstance(second.left, Attribute)
    assert second.left.attr == "price"
    assert isinstance(second.comparators[0], Constant)
    assert second.comparators[0].value == 5


def test_normalize_chained_comparisons_with_folded_negative_literal():
    tree = parse("lambda x: -10 < x.temperature <= 20")
    tree = _FoldUnaryNumericConstants().visit(tree)
    transformed = _NormalizeComparisonConstants().visit(tree)
    body = transformed.body[0].value.body

    assert isinstance(body, BoolOp)
    assert isinstance(body.op, ast.And)
    assert len(body.values) == 2

    first = body.values[0]
    assert isinstance(first, Compare)
    assert isinstance(first.ops[0], Gt)
    assert isinstance(first.left, Attribute)
    assert first.left.attr == "temperature"
    assert first.comparators[0].value == -10

    second = body.values[1]
    assert isinstance(second, Compare)
    assert isinstance(second.ops[0], LtE)
    assert isinstance(second.left, Attribute)
    assert second.left.attr == "temperature"
    assert second.comparators[0].value == 20


def test_chroma_build_filter_normalized_comparisons(numeric_definition):
    collection = ChromaCollection(
        collection_name="temps",
        record_type=dict,
        definition=numeric_definition,
        client=MagicMock(spec=ClientAPI),
    )
    assert collection._build_filter("lambda x: 5 > x.price") == {"price": {"$lt": 5}}
    assert collection._build_filter("lambda x: 0 <= x.price < 5") == {
        "$and": [{"price": {"$gte": 0}}, {"price": {"$lt": 5}}]
    }


def test_qdrant_build_filter_normalized_comparisons(numeric_definition):
    collection = QdrantCollection(
        collection_name="temps",
        record_type=dict,
        definition=numeric_definition,
        client=MagicMock(spec=AsyncQdrantClient),
    )
    assert collection._build_filter("lambda x: 5 > x.price") == FieldCondition(key="price", range=Range(lt=5.0))
    assert collection._build_filter("lambda x: 0 <= x.price < 5") == QdrantFilter(
        must=[
            FieldCondition(key="price", range=Range(gte=0.0)),
            FieldCondition(key="price", range=Range(lt=5.0)),
        ]
    )


def test_weaviate_build_filter_normalized_comparisons(numeric_definition):
    collection = WeaviateCollection(
        collection_name="temps",
        record_type=dict,
        definition=numeric_definition,
        async_client=AsyncMock(spec=WeaviateAsyncClient),
    )
    assert collection._build_filter("lambda x: 5 > x.price") == WeaviateFilter.by_property("price").less_than(5)
    parsed = collection._build_filter("lambda x: 0 <= x.price < 5")
    expected = WeaviateFilter.all_of([
        WeaviateFilter.by_property("price").greater_or_equal(0),
        WeaviateFilter.by_property("price").less_than(5),
    ])
    assert parsed.filters == expected.filters
