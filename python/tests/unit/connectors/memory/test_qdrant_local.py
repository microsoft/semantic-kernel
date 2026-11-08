# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass
from typing import Annotated

from pydantic import BaseModel
from pytest import fixture, mark

from semantic_kernel.connectors.qdrant import QdrantCollection
from semantic_kernel.data.vector import VectorStoreCollectionDefinition, VectorStoreField, vectorstoremodel


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


@dataclass
class AliasedDataclass:
    id: int
    text: str
    vector: list[float] | None = None


class AliasedModel(BaseModel):
    id: int
    text: str
    vector: list[float] | None = None


def _aliased_definition() -> VectorStoreCollectionDefinition:
    return VectorStoreCollectionDefinition(
        fields=[
            VectorStoreField("key", name="id", type="int", storage_name="point_id"),
            VectorStoreField("data", name="text", type="str", storage_name="doc_text", is_indexed=True),
            VectorStoreField("vector", name="vector", dimensions=2, type="float", storage_name="doc_vector"),
        ]
    )


@mark.parametrize("named_vectors", [True, False], ids=["named_vectors", "unnamed_vectors"])
@mark.parametrize("record_type", [dict, AliasedDataclass, AliasedModel])
async def test_local_storage_names_round_trip(record_type, named_vectors):
    def make(record_id: int, text: str, vector: list[float]):
        values = {"id": record_id, "text": text, "vector": vector}
        return values if record_type is dict else record_type(**values)

    def as_dict(record):
        return (
            record
            if isinstance(record, dict)
            else vars(record)
            if record_type is AliasedDataclass
            else record.model_dump()
        )

    async with QdrantCollection(
        record_type=record_type,
        definition=_aliased_definition(),
        collection_name="test",
        location=":memory:",
        named_vectors=named_vectors,
    ) as collection:
        await collection.ensure_collection_exists()
        await collection.upsert([make(1, "a", [1.0, 0.0]), make(2, "b", [0.0, 1.0])])

        stored = as_dict(await collection.get(1, include_vectors=True))
        assert stored == {"id": 1, "text": "a", "vector": [1.0, 0.0]}

        results = await collection.search(vector=[0.0, 1.0], include_vectors=True)
        found = [as_dict(r.record) async for r in results.results]
        assert [r["id"] for r in found] == [2, 1]
        assert found[0] == {"id": 2, "text": "b", "vector": [0.0, 1.0]}

        # filters use the storage names, so the payload must be stored under them for every record type
        results = await collection.search(vector=[0.0, 1.0], filter="lambda x: x.doc_text == 'a'")
        assert [as_dict(r.record)["id"] async for r in results.results] == [1]
