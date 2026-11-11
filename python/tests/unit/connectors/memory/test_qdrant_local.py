# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass
from typing import Annotated

from pytest import fixture, mark

from semantic_kernel.connectors.qdrant import QdrantCollection, _match_value
from semantic_kernel.data.vector import VectorStoreField, vectorstoremodel


@vectorstoremodel
@dataclass
class Record:
    id: Annotated[int, VectorStoreField("key")]
    text: Annotated[str, VectorStoreField("data", is_full_text_indexed=True)]
    temperature: Annotated[int, VectorStoreField("data", is_indexed=True)]
    vector: Annotated[list[float] | None, VectorStoreField("vector", dimensions=2)] = None


async def _populated_collection(named_vectors: bool):
    async with QdrantCollection(
        record_type=Record, collection_name="test", location=":memory:", named_vectors=named_vectors
    ) as collection:
        await collection.ensure_collection_exists()
        await collection.upsert([
            Record(1, "a", 1, [1.0, 0.2]),
            Record(2, "a", 5, [0.0, 1.0]),
            Record(3, "a", 9, [1.0, 1.0]),
        ])
        yield collection


@fixture(params=[True, False], ids=["named_vectors", "unnamed_vectors"])
async def local_collection(request):
    async for collection in _populated_collection(request.param):
        yield collection


@fixture
async def named_local_collection():
    async for collection in _populated_collection(True):
        yield collection


async def test_local_vector_search(local_collection):
    results = await local_collection.search(vector=[1.0, 1.0])
    assert [r.record.id async for r in results.results] == [3, 1, 2]


async def test_local_vector_search_single_comparison_filter(local_collection):
    results = await local_collection.search(vector=[1.0, 1.0], filter="lambda x: x.temperature > 1")
    assert [r.record.id async for r in results.results] == [3, 2]


async def test_local_hybrid_search_single_comparison_filter(named_local_collection):
    results = await named_local_collection.hybrid_search(
        values=["a"],
        vector=[1.0, 1.0],
        additional_property_name="text",
        filter="lambda x: x.temperature > 1",
    )
    assert sorted([r.record.id async for r in results.results]) == [2, 3]


@vectorstoremodel
@dataclass
class Product:
    id: Annotated[int, VectorStoreField("key")]
    price: Annotated[float, VectorStoreField("data", is_indexed=True)]
    in_stock: Annotated[bool, VectorStoreField("data", is_indexed=True)]
    vector: Annotated[list[float] | None, VectorStoreField("vector", dimensions=2)] = None


@fixture
async def product_collection():
    async with QdrantCollection(record_type=Product, collection_name="products", location=":memory:") as collection:
        await collection.ensure_collection_exists()
        await collection.upsert([Product(1, 4.5, True, [1.0, 0.0]), Product(2, 5.0, False, [0.0, 1.0])])
        yield collection


@mark.parametrize(
    ("filter_str", "expected"),
    [
        # MatchValue rejects floats, and an int never matched a float payload
        ("lambda x: x.price == 4.5", [1]),
        ("lambda x: x.price != 4.5", [2]),
        ("lambda x: x.price == 5", [2]),
        # MatchAny only accepts lists of str or int
        ("lambda x: x.price in [4.5, 9.0]", [1]),
        ("lambda x: x.price not in [4.5]", [2]),
        ("lambda x: x.in_stock in [True]", [1]),
        ("lambda x: x.in_stock not in [True]", [2]),
        # Large floats too, which MatchValue would reject
        ("lambda x: x.price == 1e20", []),
        ("lambda x: x.price != 1e20", [1, 2]),
    ],
)
async def test_local_filter_with_float_and_bool_values(product_collection, filter_str, expected):
    results = await product_collection.search(vector=[1.0, 1.0], filter=filter_str)
    assert sorted([r.record.id async for r in results.results]) == expected


@mark.parametrize(
    ("value", "uses_range"),
    [(2**53 - 1, True), (-(2**53) + 1, True), (2**53, False), (2**60, False), (1e20, True)],
)
def test_match_value_uses_range_only_where_float64_is_exact(value, uses_range):
    # The server compares ranges as float64, where 2**53 and 2**53 + 1 are the same value
    condition = _match_value("n", value)
    assert (condition.range is not None) is uses_range
    assert (condition.match is None) is uses_range
