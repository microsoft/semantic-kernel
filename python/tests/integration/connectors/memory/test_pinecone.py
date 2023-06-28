# Copyright (c) Microsoft. All rights reserved.

import os

import numpy as np
import pytest

import semantic_kernel as sk
from semantic_kernel.connectors.memory.pinecone import PineconeMemoryStore
from semantic_kernel.memory.memory_record import MemoryRecord

try:
    import pinecone  # noqa: F401

    pinecone_installed = True
except ImportError:
    pinecone_installed = False

pytestmark = pytest.mark.skipif(
    not pinecone_installed, reason="pinecone is not installed"
)


@pytest.fixture(scope="session")
def get_pinecone_config():
    if "Python_Integration_Tests" in os.environ:
        api_key = os.environ["Pinecone__ApiKey"]
        org_id = None
    else:
        # Load credentials from .env file
        api_key, org_id = sk.pinecone_settings_from_dot_env()

    return api_key, org_id


@pytest.fixture
def memory_record1():
    return MemoryRecord(
        id="test_id1",
        text="sample text1",
        is_reference=False,
        embedding=np.array([0.5, 0.5]),
        description="description",
        additional_metadata="additional metadata",
        external_source_name="external source",
        timestamp="timestamp",
    )


@pytest.fixture
def memory_record2():
    return MemoryRecord(
        id="test_id2",
        text="sample text2",
        is_reference=False,
        embedding=np.array([0.25, 0.75]),
        description="description",
        additional_metadata="additional metadata",
        external_source_name="external source",
        timestamp="timestamp",
    )


@pytest.fixture
def memory_record3():
    return MemoryRecord(
        id="test_id3",
        text="sample text3",
        is_reference=False,
        embedding=np.array([0.25, 0.80]),
        description="description",
        additional_metadata="additional metadata",
        external_source_name="external source",
        timestamp="timestamp",
    )


def test_constructor(get_pinecone_config):
    api_key, environment = get_pinecone_config
    memory = PineconeMemoryStore(api_key, environment, 2)
    assert memory.get_collections() is not None


@pytest.mark.asyncio
async def test_create_and_get_collection_async(get_pinecone_config):
    api_key, environment = get_pinecone_config
    memory = PineconeMemoryStore(api_key, environment, 2)

    await memory.create_collection_async("test-collection")
    result = await memory.describe_collection_async("test-collection")
    assert result is not None
    assert result.name == "test-collection"


@pytest.mark.asyncio
async def test_get_collections_async(get_pinecone_config):
    api_key, environment = get_pinecone_config
    memory = PineconeMemoryStore(api_key, environment, 2)

    await memory.create_collection_async("test-collection", 2)
    result = await memory.get_collections_async()
    assert "test-collection" in result


@pytest.mark.asyncio
async def test_delete_collection_async(get_pinecone_config):
    api_key, environment = get_pinecone_config
    memory = PineconeMemoryStore(api_key, environment, 2)

    await memory.create_collection_async("test-collection")
    await memory.delete_collection_async("test-collection")
    result = await memory.get_collections_async()
    assert "test-collection" not in result


@pytest.mark.asyncio
async def test_does_collection_exist_async(get_pinecone_config):
    api_key, environment = get_pinecone_config
    memory = PineconeMemoryStore(api_key, environment, 2)

    await memory.create_collection_async("test-collection")
    result = await memory.does_collection_exist_async("test-collection")
    assert result is True


@pytest.mark.asyncio
async def test_upsert_async_and_get_async(get_pinecone_config, memory_record1):
    api_key, environment = get_pinecone_config
    memory = PineconeMemoryStore(api_key, environment, 2)

    await memory.create_collection_async("test-collection")
    await memory.upsert_async("test-collection", memory_record1)

    result = await memory.get_async(
        "test-collection",
        memory_record1._id,
        with_embedding=True,
    )

    assert result is not None
    assert result._id == memory_record1._id
    assert result._description == memory_record1._description
    assert result._text == memory_record1._text
    assert result.embedding is not None


@pytest.mark.asyncio
async def test_upsert_batch_async_and_get_batch_async(
    get_pinecone_config, memory_record1, memory_record2
):
    api_key, environment = get_pinecone_config
    memory = PineconeMemoryStore(api_key, environment, 2)

    await memory.create_collection_async("test-collection")
    await memory.upsert_batch_async("test-collection", [memory_record1, memory_record2])

    results = await memory.get_batch_async(
        "test-collection",
        [memory_record1._id, memory_record2._id],
        with_embeddings=True,
    )

    assert len(results) >= 2
    assert results[0]._id in [memory_record1._id, memory_record2._id]
    assert results[1]._id in [memory_record1._id, memory_record2._id]


@pytest.mark.asyncio
async def test_remove_async(get_pinecone_config, memory_record1):
    api_key, environment = get_pinecone_config
    memory = PineconeMemoryStore(api_key, environment, 2)

    await memory.create_collection_async("test-collection")
    await memory.upsert_async("test-collection", memory_record1)
    await memory.remove_async("test-collection", memory_record1._id)

    with pytest.raises(KeyError):
        _ = await memory.get_async(
            "test-collection", memory_record1._id, with_embedding=True
        )


@pytest.mark.asyncio
async def test_remove_batch_async(get_pinecone_config, memory_record1, memory_record2):
    api_key, environment = get_pinecone_config
    memory = PineconeMemoryStore(api_key, environment, 2)

    await memory.create_collection_async("test-collection")
    await memory.upsert_batch_async("test-collection", [memory_record1, memory_record2])
    await memory.remove_batch_async(
        "test-collection", [memory_record1._id, memory_record2._id]
    )

    with pytest.raises(KeyError):
        _ = await memory.get_async(
            "test-collection", memory_record1._id, with_embedding=True
        )

    with pytest.raises(KeyError):
        _ = await memory.get_async(
            "test-collection", memory_record2._id, with_embedding=True
        )


@pytest.mark.asyncio
async def test_get_nearest_match_async(
    get_pinecone_config, memory_record1, memory_record2
):
    api_key, environment = get_pinecone_config
    memory = PineconeMemoryStore(api_key, environment, 2)

    await memory.create_collection_async("test-collection")
    await memory.upsert_batch_async("test-collection", [memory_record1, memory_record2])

    test_embedding = memory_record1.embedding
    test_embedding[0] = test_embedding[0] + 0.01

    result = await memory.get_nearest_match_async(
        "test-collection", test_embedding, min_relevance_score=0.0, with_embedding=True
    )

    assert result is not None
    assert result[0]._id == memory_record1._id


@pytest.mark.asyncio
async def test_get_nearest_matches_async(
    get_pinecone_config, memory_record1, memory_record2, memory_record3
):
    api_key, environment = get_pinecone_config
    memory = PineconeMemoryStore(api_key, environment, 2)

    await memory.create_collection_async("test-collection")
    await memory.upsert_batch_async(
        "test-collection", [memory_record1, memory_record2, memory_record3]
    )

    test_embedding = memory_record2.embedding
    test_embedding[0] = test_embedding[0] + 0.025

    result = await memory.get_nearest_matches_async(
        "test-collection",
        test_embedding,
        limit=2,
        min_relevance_score=0.0,
        with_embeddings=True,
    )

    assert len(result) == 2
    assert result[0][0]._id in [memory_record3._id, memory_record2._id]
    assert result[1][0]._id in [memory_record3._id, memory_record2._id]
