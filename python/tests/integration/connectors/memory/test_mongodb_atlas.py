# Copyright (c) Microsoft. All rights reserved.

import asyncio
import random

import numpy as np
import pytest
import pytest_asyncio

from semantic_kernel.connectors.memory.mongodb_atlas.mongodb_atlas_memory_store import (
    MongoDBAtlasMemoryStore,
)
from semantic_kernel.exceptions import MemoryConnectorInitializationError
from semantic_kernel.memory.memory_record import MemoryRecord

mongodb_atlas_installed: bool
try:
    import motor  # noqa: F401
    from pymongo import errors

    mongodb_atlas_installed = True
except ImportError:
    mongodb_atlas_installed = False

pytestmark = pytest.mark.skipif(
    not mongodb_atlas_installed,
    reason="MongoDB Atlas Vector Search not installed; pip install motor",
)
DUPLICATE_INDEX_ERR_CODE = 68
READ_ONLY_COLLECTION = "nearestSearch"
DIMENSIONS = 3


def is_equal_memory_record(
    mem1: MemoryRecord, mem2: MemoryRecord, with_embeddings: bool
):
    """Comparator for two memory records"""

    def dictify_memory_record(mem):
        return {k: v for k, v in mem.__dict__.items() if k != "_embedding"}

    assert dictify_memory_record(mem1) == dictify_memory_record(mem2)
    if with_embeddings:
        assert mem1._embedding.tolist() == mem2._embedding.tolist()


@pytest.fixture
def memory_record_gen():
    def memory_record(_id):
        return MemoryRecord(
            id=str(_id),
            text=f"{_id} text",
            is_reference=False,
            embedding=np.array([1 / (_id + val) for val in range(0, DIMENSIONS)]),
            description=f"{_id} description",
            external_source_name=f"{_id} external source",
            additional_metadata=f"{_id} additional metadata",
            timestamp=None,
            key=str(_id),
        )

    return memory_record


@pytest.fixture
def test_collection():
    return f"AVSTest-{random.randint(0, 9999)}"


@pytest.fixture
def memory():
    try:
        return MongoDBAtlasMemoryStore(database_name="pyMSKTest")
    except MemoryConnectorInitializationError:
        pytest.skip("MongoDB Atlas connection string not found in env vars.")


@pytest_asyncio.fixture
async def vector_search_store(memory):
    await memory.__aenter__()
    try:
        # Delete all collections before and after
        for cname in await memory.get_collections():
            await memory.delete_collection(cname)

        def patch_index_exception(fn):
            """Function patch for collection creation call to retry
            on duplicate index errors
            """

            async def _patch(collection_name):
                while True:
                    try:
                        await fn(collection_name)
                        break
                    except errors.OperationFailure as e:
                        # In this test instance, this error code is indicative
                        # of a previous index not completing teardown
                        if e.code != DUPLICATE_INDEX_ERR_CODE:
                            raise
                        await asyncio.sleep(1)

            return _patch

        memory.create_collection = patch_index_exception(memory.create_collection)

        try:
            yield memory
        finally:
            for cname in await memory.get_collections():
                await memory.delete_collection(cname)
    except Exception:
        pass
    finally:
        await memory.__aexit__(None, None, None)


@pytest_asyncio.fixture
async def nearest_match_store(memory):
    """Fixture for read only vector store; the URI for test needs atlas configured"""
    await memory.__aenter__()
    try:
        if not await memory.does_collection_exist("nearestSearch"):
            pytest.skip(
                reason="db: readOnly collection: nearestSearch not found, "
                "please ensure your Atlas Test Cluster has this collection configured"
            )
        yield memory
    except Exception:
        pass
    finally:
        await memory.__aexit__(None, None, None)


@pytest.mark.asyncio
async def test_constructor(memory):
    assert isinstance(memory, MongoDBAtlasMemoryStore)


@pytest.mark.asyncio
async def test_collection_create_and_delete(vector_search_store, test_collection):
    await vector_search_store.create_collection(test_collection)
    assert await vector_search_store.does_collection_exist(test_collection)
    await vector_search_store.delete_collection(test_collection)
    assert not await vector_search_store.does_collection_exist(test_collection)


@pytest.mark.asyncio
async def test_collection_upsert(
    vector_search_store, test_collection, memory_record_gen
):
    mems = [memory_record_gen(i) for i in range(1, 4)]
    mem1 = await vector_search_store.upsert(test_collection, mems[0])
    assert mem1 == mems[0]._id


@pytest.mark.asyncio
async def test_collection_batch_upsert(
    vector_search_store, test_collection, memory_record_gen
):
    mems = [memory_record_gen(i) for i in range(1, 4)]
    mems_check = await vector_search_store.upsert_batch(test_collection, mems)
    assert [m._id for m in mems] == mems_check


@pytest.mark.asyncio
async def test_collection_deletion(
    vector_search_store, test_collection, memory_record_gen
):
    mem = memory_record_gen(1)
    await vector_search_store.upsert(test_collection, mem)
    insertion_val = await vector_search_store.get(test_collection, mem._id, True)
    assert mem._id == insertion_val._id
    assert mem._embedding.tolist() == insertion_val._embedding.tolist()
    assert insertion_val is not None
    await vector_search_store.remove(test_collection, mem._id)
    val = await vector_search_store.get(test_collection, mem._id, False)
    assert val is None


@pytest.mark.asyncio
async def test_collection_batch_deletion(
    vector_search_store, test_collection, memory_record_gen
):
    mems = [memory_record_gen(i) for i in range(1, 4)]
    await vector_search_store.upsert_batch(test_collection, mems)
    ids = [mem._id for mem in mems]
    insertion_val = await vector_search_store.get_batch(test_collection, ids, True)
    assert len(insertion_val) == len(mems)
    await vector_search_store.remove_batch(test_collection, ids)
    assert not await vector_search_store.get_batch(test_collection, ids, False)


@pytest.mark.asyncio
async def test_collection_get(vector_search_store, test_collection, memory_record_gen):
    mem = memory_record_gen(1)
    await vector_search_store.upsert(test_collection, mem)
    insertion_val = await vector_search_store.get(test_collection, mem._id, False)
    is_equal_memory_record(mem, insertion_val, False)

    refetched_record = await vector_search_store.get(test_collection, mem._id, True)
    is_equal_memory_record(mem, refetched_record, True)


@pytest.mark.asyncio
async def test_collection_batch_get(
    vector_search_store, test_collection, memory_record_gen
):
    mems = {str(i): memory_record_gen(i) for i in range(1, 4)}
    await vector_search_store.upsert_batch(test_collection, list(mems.values()))
    insertion_val = await vector_search_store.get_batch(
        test_collection, list(mems.keys()), False
    )
    assert len(insertion_val) == len(mems)
    for val in insertion_val:
        is_equal_memory_record(mems[val._id], val, False)

    refetched_vals = await vector_search_store.get_batch(
        test_collection, list(mems.keys()), True
    )
    for ref in refetched_vals:
        is_equal_memory_record(mems[ref._id], ref, True)


@pytest.mark.asyncio
async def test_collection_knn_match(nearest_match_store, memory_record_gen):
    mem = memory_record_gen(7)
    await nearest_match_store.upsert(READ_ONLY_COLLECTION, mem)
    result, score = await nearest_match_store.get_nearest_match(
        collection_name=READ_ONLY_COLLECTION,
        embedding=mem._embedding,
        with_embedding=True,
    )
    is_equal_memory_record(mem, result, True)
    assert score


@pytest.mark.asyncio
async def test_collection_knn_match_with_score(nearest_match_store, memory_record_gen):
    mem = memory_record_gen(7)
    await nearest_match_store.upsert(READ_ONLY_COLLECTION, mem)
    result, score = await nearest_match_store.get_nearest_match(
        collection_name=READ_ONLY_COLLECTION,
        embedding=mem._embedding,
        with_embedding=True,
        min_relevance_score=0.0,
    )
    is_equal_memory_record(mem, result, True)
    assert score


async def knn_matcher(
    nearest_match_store,
    test_collection,
    mems,
    query_limit,
    expected_limit,
    min_relevance_score,
):
    results_and_scores = await nearest_match_store.get_nearest_matches(
        collection_name=test_collection,
        embedding=mems["2"]._embedding,
        limit=query_limit,
        with_embeddings=True,
        min_relevance_score=min_relevance_score,
    )
    assert len(results_and_scores) == expected_limit
    scores = [score for _, score in results_and_scores]
    assert scores == sorted(scores, reverse=True)
    for result, _ in results_and_scores:
        is_equal_memory_record(mems[result._id], result, True)


@pytest.mark.asyncio
async def test_collection_knn_matches(nearest_match_store, memory_record_gen):
    mems = {str(i): memory_record_gen(i) for i in range(1, 4)}
    await nearest_match_store.upsert_batch(READ_ONLY_COLLECTION, mems.values())
    await knn_matcher(
        nearest_match_store,
        READ_ONLY_COLLECTION,
        mems,
        query_limit=2,
        expected_limit=2,
        min_relevance_score=None,
    )


@pytest.mark.asyncio
async def test_collection_knn_matches_with_score(
    nearest_match_store, memory_record_gen
):
    mems = {str(i): memory_record_gen(i) for i in range(1, 4)}
    await nearest_match_store.upsert_batch(READ_ONLY_COLLECTION, mems.values())
    await knn_matcher(
        nearest_match_store,
        READ_ONLY_COLLECTION,
        mems,
        query_limit=2,
        expected_limit=2,
        min_relevance_score=0.0,
    )
