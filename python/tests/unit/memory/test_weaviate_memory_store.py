import numpy as np
import pytest

from semantic_kernel.memory import weaviate_memory_store
from semantic_kernel.memory.memory_record import MemoryRecord


@pytest.fixture
def documents():
    records = []

    records.append(
        MemoryRecord.local_record(
            "1",
            "The quick brown fox jumps over the lazy dog.",
            "A classic pangram.",
            np.array([0.1, 0.1]),
        )
    )
    records.append(
        MemoryRecord.local_record(
            "2",
            "The five boxing wizards jump quickly.",
            "Another popular pangram.",
            np.array([0.1, 0.11]),
        )
    )
    records.append(
        MemoryRecord.local_record(
            "3",
            "Pack my box with five dozen liquor jugs.",
            "A useful pangram.",
            np.array([0.11, 0.1]),
        )
    )

    records.append(
        MemoryRecord.local_record(
            "4",
            "Lorem ipsum dolor sit amet.",
            "A common placeholder text.",
            np.array([10, 10]),
        )
    )
    records.append(
        MemoryRecord.local_record(
            "5",
            "Etiam faucibus orci vitae lacus pellentesque.",
            "A Latin text.",
            np.array([10.1, 10.2]),
        )
    )

    yield records


@pytest.fixture
def memory_store():
    config = weaviate_memory_store.WeaviateConfig(use_embed=True)
    store = weaviate_memory_store.WeaviateMemoryStore(config)
    store.client.schema.delete_all()
    yield store
    store.client.schema.delete_all()


@pytest.fixture
def memory_store_with_empty_collection(memory_store, event_loop):
    collection_name = "MindRepository"
    event_loop.run_until_complete(memory_store.create_collection_async(collection_name))
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
