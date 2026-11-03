# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass
from typing import Annotated

from pytest import fixture

from semantic_kernel.connectors.qdrant import QdrantCollection
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
