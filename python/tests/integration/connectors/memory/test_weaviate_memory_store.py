# Copyright (c) Microsoft. All rights reserved.

import sys
import time

import numpy as np
import numpy.testing as npt
import pytest

from semantic_kernel.connectors.memory.weaviate import weaviate_memory_store
from semantic_kernel.memory.memory_record import MemoryRecord

if not sys.platform.startswith("linux"):
    pytest.skip(
        "test_weaviate_memory_store uses embedded weaviate which only runs on Linux at the moment",
        allow_module_level=True,
    )


@pytest.fixture
def documents():
    records = []

    records.append(
        MemoryRecord.local_record(
            "1",
            "The quick brown fox jumps over the lazy dog.",
            "A classic pangram.",
            "additional info",
            np.array([0.1, 0.1]),
        )
    )
    records.append(
        MemoryRecord.local_record(
            "2",
            "The five boxing wizards jump quickly.",
            "Another popular pangram.",
            "additional info",
            np.array([0.1, 0.11]),
        )
    )
    records.append(
        MemoryRecord.local_record(
            "3",
            "Pack my box with five dozen liquor jugs.",
            "A useful pangram.",
            "additional info",
            np.array([0.11, 0.1]),
        )
    )

    records.append(
        MemoryRecord.local_record(
            "4",
            "Lorem ipsum dolor sit amet.",
            "A common placeholder text.",
            "additional info",
            np.array([-10, -10]),
        )
    )
    records.append(
        MemoryRecord.local_record(
            "5",
            "Etiam faucibus orci vitae lacus pellentesque.",
            "A Latin text.",
            "additional info",
            np.array([-10.1, -10.2]),
        )
    )

    yield records


@pytest.fixture
def memory_store():
    max_attempts = 5  # the number of retry attempts
    delay = 30  # delay in seconds between each attempt

    config = weaviate_memory_store.WeaviateConfig(use_embed=True)
    for attempt in range(max_attempts):
        try:
            store = weaviate_memory_store.WeaviateMemoryStore(config)
            store.client.schema.delete_all()
        except Exception:
            if attempt < max_attempts - 1:  # it's not the final attempt
                time.sleep(delay)  # wait before retrying
                continue  # go to the next attempt
            else:  # it's the final attempt
                raise  # re-raise the last exception
        else:
            break  # successful attempt, get out of the loop

    yield store

    store.client.schema.delete_all()


@pytest.fixture
def memory_store_with_empty_collection(memory_store, event_loop):
    collection_name = "MindRepository"
    event_loop.run_until_complete(memory_store.create_collection_async(collection_name))
    return collection_name, memory_store


@pytest.fixture
def memory_store_with_collection(memory_store, event_loop, documents):
    collection_name = "BigMemory"
    event_loop.run_until_complete(memory_store.create_collection_async(collection_name))

    keys = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
    for document, key in zip(documents, keys):
        document._key = key
        event_loop.run_until_complete(
            memory_store.upsert_async(collection_name, document)
        )

    return collection_name, memory_store


def test_embedded_weaviate():
    config = weaviate_memory_store.WeaviateConfig(use_embed=True)
    memory_store = weaviate_memory_store.WeaviateMemoryStore(config=config)

    assert memory_store.client._connection.embedded_db


@pytest.mark.asyncio
async def test_create_collection(memory_store):
    collection_name = "MemoryVault"
    await memory_store.create_collection_async(collection_name)

    assert memory_store.client.schema.get(collection_name)


@pytest.mark.asyncio
async def test_get_collections(memory_store):
    collection_names = ["MemoryVault", "ThoughtArchive"]

    for collection_name in collection_names:
        await memory_store.create_collection_async(collection_name)

    results = await memory_store.get_collections_async()

    assert set(results) == set(collection_names)


@pytest.mark.asyncio
async def test_delete_collection(memory_store_with_empty_collection):
    collection_name, memory_store = memory_store_with_empty_collection

    schemas = memory_store.client.schema.get()["classes"]
    assert len(schemas) == 1

    await memory_store.delete_collection_async(collection_name)

    schemas = memory_store.client.schema.get()["classes"]
    assert len(schemas) == 0


@pytest.mark.asyncio
async def test_collection_exists(memory_store_with_empty_collection):
    collection_name, memory_store = memory_store_with_empty_collection

    memory_store.client.schema.get()["classes"]

    assert await memory_store.does_collection_exist_async(collection_name)
    assert not await memory_store.does_collection_exist_async("NotACollection")


@pytest.mark.asyncio
async def test_upsert(memory_store_with_empty_collection, documents):
    collection_name, memory_store = memory_store_with_empty_collection

    for doc in documents[:2]:
        await memory_store.upsert_async(collection_name, doc)

    total_docs = memory_store.client.data_object.get(class_name=collection_name)[
        "totalResults"
    ]
    assert total_docs == 2


@pytest.mark.asyncio
async def test_upsert_batch(memory_store_with_empty_collection, documents):
    collection_name, memory_store = memory_store_with_empty_collection

    await memory_store.upsert_batch_async(collection_name, documents)

    total_docs = memory_store.client.data_object.get(class_name=collection_name)[
        "totalResults"
    ]
    assert total_docs == len(documents)


@pytest.mark.asyncio
async def test_get(memory_store_with_collection, documents):
    collection_name, memory_store = memory_store_with_collection

    key = "Alpha"

    expected_result = [doc for doc in documents if doc._key == key][0]
    actual_result = await memory_store.get_async(
        collection_name, key, with_embedding=True
    )
    npt.assert_equal(expected_result.__dict__, actual_result.__dict__)

    actual_result = await memory_store.get_async(
        collection_name, key, with_embedding=False
    )
    expected_result.__dict__["_embedding"] = None
    npt.assert_equal(expected_result.__dict__, actual_result.__dict__)

    key = "NotInCollection"
    actual_result = await memory_store.get_async(
        collection_name, key, with_embedding=True
    )

    assert actual_result is None


@pytest.mark.asyncio
async def test_get_batch(memory_store_with_collection, documents):
    collection_name, memory_store = memory_store_with_collection

    keys = ["Alpha", "Beta", "Gamma"]

    expected_results = [doc for doc in documents if doc._key in keys]

    actual_results = await memory_store.get_batch_async(
        collection_name, keys, with_embedding=True
    )

    for expected, actual in zip(expected_results, actual_results):
        npt.assert_equal(expected.__dict__, actual.__dict__)

    actual_results = await memory_store.get_batch_async(
        collection_name, keys, with_embedding=False
    )

    for expected, actual in zip(expected_results, actual_results):
        expected.__dict__["_embedding"] = None
        npt.assert_equal(expected.__dict__, actual.__dict__)


@pytest.mark.asyncio
async def test_remove_batch(memory_store_with_collection, documents):
    collection_name, memory_store = memory_store_with_collection

    keys = ["Alpha", "Beta", "Gamma"]

    await memory_store.remove_batch_async(collection_name, keys)

    remaining_docs = memory_store.client.data_object.get(class_name=collection_name)[
        "totalResults"
    ]
    assert remaining_docs == len(documents) - len(keys)


@pytest.mark.asyncio
async def test_remove(memory_store_with_collection, documents):
    collection_name, memory_store = memory_store_with_collection

    key = "Alpha"

    await memory_store.remove_async(collection_name, key)

    remaining_docs = memory_store.client.data_object.get(class_name=collection_name)[
        "totalResults"
    ]
    assert remaining_docs == len(documents) - 1


@pytest.mark.asyncio
async def test_get_nearest_matches(memory_store_with_collection, documents):
    collection_name, memory_store = memory_store_with_collection

    search_query = np.array([-10, -10])
    min_relevance_score = 0.9
    limit = 4

    expected_result = [documents[3], documents[4]]
    actual_result = await memory_store.get_nearest_matches_async(
        collection_name, search_query, limit, min_relevance_score, with_embeddings=True
    )
    actual_docss, _ = list(zip(*actual_result))

    assert len(actual_result) == len(expected_result)
    for expected, actual in zip(expected_result, actual_docss):
        npt.assert_equal(expected.__dict__, actual.__dict__)

    actual_result = await memory_store.get_nearest_matches_async(
        collection_name, search_query, limit, min_relevance_score, with_embeddings=False
    )
    actual_docss, _ = list(zip(*actual_result))

    assert len(actual_result) == len(expected_result)
    for expected, actual in zip(expected_result, actual_docss):
        expected.__dict__["_embedding"] = None
        npt.assert_equal(expected.__dict__, actual.__dict__)


@pytest.mark.asyncio
async def test_get_nearest_match(memory_store_with_collection, documents):
    collection_name, memory_store = memory_store_with_collection

    search_query = np.array([-10, -10])
    min_relevance_score = 0.9

    expected_result = documents[3]
    actual_result = await memory_store.get_nearest_match_async(
        collection_name, search_query, min_relevance_score, with_embedding=True
    )

    npt.assert_equal(expected_result.__dict__, actual_result[0].__dict__)

    actual_result = await memory_store.get_nearest_match_async(
        collection_name, search_query, min_relevance_score, with_embedding=False
    )

    expected_result.__dict__["_embedding"] = None
    npt.assert_equal(expected_result.__dict__, actual_result[0].__dict__)
