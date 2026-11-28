# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass
from typing import Annotated

from pytest import approx, fixture

from semantic_kernel.connectors.in_memory import InMemoryCollection
from semantic_kernel.connectors.qdrant import QdrantCollection
from semantic_kernel.data.vector import DistanceFunction, VectorStoreField, vectorstoremodel


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


async def test_default_score_semantics_match_in_memory():
    @vectorstoremodel
    @dataclass
    class ScoreRecord:
        id: Annotated[int, VectorStoreField("key")]
        tag: Annotated[str, VectorStoreField("data")]
        vector: Annotated[list[float] | None, VectorStoreField("vector", dimensions=4)] = None

    docs = [
        ScoreRecord(1, "exact", [1.0, 0.0, 0.0, 0.0]),
        ScoreRecord(2, "ortho", [0.0, 1.0, 0.0, 0.0]),
        ScoreRecord(3, "opposite", [-1.0, 0.0, 0.0, 0.0]),
    ]
    query = [1.0, 0.0, 0.0, 0.0]

    async with (
        QdrantCollection(record_type=ScoreRecord, collection_name="score_test", location=":memory:") as qdrant,
        InMemoryCollection(record_type=ScoreRecord, collection_name="score_test") as in_mem,
    ):
        await qdrant.ensure_collection_exists()
        await in_mem.ensure_collection_exists()
        await qdrant.upsert(docs)
        await in_mem.upsert(docs)

        q_res = {r.record.tag: r.score async for r in (await qdrant.search(vector=query, top=3)).results}
        m_res = {r.record.tag: r.score async for r in (await in_mem.search(vector=query, top=3)).results}

        assert q_res["exact"] == approx(0.0, abs=1e-5)
        assert q_res["ortho"] == approx(1.0, abs=1e-5)
        assert q_res["opposite"] == approx(2.0, abs=1e-5)
        for tag in ("exact", "ortho", "opposite"):
            assert q_res[tag] == approx(m_res[tag], abs=1e-5)


async def test_explicit_cosine_distance_and_similarity_scores():
    @vectorstoremodel
    @dataclass
    class DistRecord:
        id: Annotated[int, VectorStoreField("key")]
        tag: Annotated[str, VectorStoreField("data")]
        vector: Annotated[
            list[float] | None,
            VectorStoreField("vector", dimensions=4, distance_function=DistanceFunction.COSINE_DISTANCE),
        ] = None

    @vectorstoremodel
    @dataclass
    class SimRecord:
        id: Annotated[int, VectorStoreField("key")]
        tag: Annotated[str, VectorStoreField("data")]
        vector: Annotated[
            list[float] | None,
            VectorStoreField("vector", dimensions=4, distance_function=DistanceFunction.COSINE_SIMILARITY),
        ] = None

    query = [1.0, 0.0, 0.0, 0.0]
    async with (
        QdrantCollection(record_type=DistRecord, collection_name="dist_test", location=":memory:") as dist_col,
        QdrantCollection(record_type=SimRecord, collection_name="sim_test", location=":memory:") as sim_col,
    ):
        await dist_col.ensure_collection_exists()
        await sim_col.ensure_collection_exists()
        await dist_col.upsert([
            DistRecord(1, "exact", [1.0, 0.0, 0.0, 0.0]),
            DistRecord(2, "opposite", [-1.0, 0.0, 0.0, 0.0]),
        ])
        await sim_col.upsert([
            SimRecord(1, "exact", [1.0, 0.0, 0.0, 0.0]),
            SimRecord(2, "opposite", [-1.0, 0.0, 0.0, 0.0]),
        ])

        d_scores = {r.record.tag: r.score async for r in (await dist_col.search(vector=query, top=2)).results}
        s_scores = {r.record.tag: r.score async for r in (await sim_col.search(vector=query, top=2)).results}

        assert d_scores["exact"] == approx(0.0, abs=1e-5)
        assert d_scores["opposite"] == approx(2.0, abs=1e-5)
        assert s_scores["exact"] == approx(1.0, abs=1e-5)
        assert s_scores["opposite"] == approx(-1.0, abs=1e-5)
