# Copyright (c) Microsoft. All rights reserved.

import asyncio
import time

import numpy as np
import pytest
from pydantic import ValidationError

from semantic_kernel.connectors.memory.pinecone import PineconeMemoryStore
from semantic_kernel.connectors.memory.pinecone.pinecone_settings import (
    PineconeSettings,
)
from semantic_kernel.exceptions.service_exceptions import ServiceResourceNotFoundError
from semantic_kernel.memory.memory_record import MemoryRecord

try:
    import pinecone

    pinecone_installed = True
except ImportError:
    pinecone_installed = False

pytestmark = pytest.mark.skipif(
    not pinecone_installed, reason="pinecone is not installed"
)


async def retry(func, retries=1):
    for i in range(retries):
        try:
            await asyncio.sleep(3)
            return await func()
        except pinecone.core.client.exceptions.ForbiddenException as e:
            print(e)
            await asyncio.sleep(i * 2)
        except pinecone.core.client.exceptions.ServiceException as e:
            print(e)
            await asyncio.sleep(i * 2)
    return None


@pytest.fixture(autouse=True, scope="module")
def slow_down_tests():
    yield
    time.sleep(3)


@pytest.fixture(scope="session")
def api_key():
    try:
        pinecone_settings = PineconeSettings.create()
        return pinecone_settings.api_key.get_secret_value()
    except ValidationError:
        pytest.skip("Pinecone API key not found in env vars.")


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


@pytest.mark.asyncio
async def test_constructor(api_key):
    memory = PineconeMemoryStore(api_key, 2)
    assert await memory.get_collections() is not None


@pytest.mark.asyncio
@pytest.mark.xfail(
    reason="Test failed due to known unreliable communications with Pinecone free tier"
)
async def test_create_and_get_collection(api_key):
    memory = PineconeMemoryStore(api_key, 2)

    await retry(lambda: memory.create_collection("test-collection"))
    result = await retry(lambda: memory.describe_collection("test-collection"))
    assert result is not None
    assert result.name == "test-collection"


@pytest.mark.asyncio
@pytest.mark.xfail(
    reason="Test failed due to known unreliable communications with Pinecone free tier"
)
async def test_get_collections(api_key):
    memory = PineconeMemoryStore(api_key, 2)

    await retry(lambda: memory.create_collection("test-collection", 2))
    result = await retry(lambda: memory.get_collections())
    assert "test-collection" in result.names()


@pytest.mark.asyncio
@pytest.mark.xfail(
    reason="Test failed due to known unreliable communications with Pinecone free tier"
)
async def test_delete_collection(api_key):
    memory = PineconeMemoryStore(api_key, 2)

    await retry(lambda: memory.create_collection("test-collection"))
    await retry(lambda: memory.delete_collection("test-collection"))
    result = await retry(lambda: memory.get_collections())
    assert "test-collection" not in result.names()


@pytest.mark.asyncio
@pytest.mark.xfail(
    reason="Test failed due to known unreliable communications with Pinecone free tier"
)
async def test_does_collection_exist(api_key):
    memory = PineconeMemoryStore(api_key, 2)

    await retry(lambda: memory.create_collection("test-collection"))
    result = await retry(lambda: memory.does_collection_exist("test-collection"))
    assert result is True


@pytest.mark.asyncio
@pytest.mark.xfail(
    reason="Test failed due to known unreliable communications with Pinecone free tier"
)
async def test_upsert_and_get(api_key, memory_record1):
    memory = PineconeMemoryStore(api_key, 2)

    await retry(lambda: memory.create_collection("test-collection"))
    await retry(lambda: memory.upsert("test-collection", memory_record1))

    result = await retry(
        lambda: memory.get(
            "test-collection",
            memory_record1._id,
            with_embedding=True,
        )
    )

    assert result is not None
    assert result._id == memory_record1._id
    assert result._description == memory_record1._description
    assert result._text == memory_record1._text
    assert result.embedding is not None


@pytest.mark.asyncio
@pytest.mark.xfail(
    reason="Test failed due to known unreliable communications with Pinecone free tier"
)
async def test_upsert_batch_and_get_batch(api_key, memory_record1, memory_record2):
    memory = PineconeMemoryStore(api_key, 2)

    await retry(lambda: memory.create_collection("test-collection"))
    await retry(
        lambda: memory.upsert_batch("test-collection", [memory_record1, memory_record2])
    )

    results = await retry(
        lambda: memory.get_batch(
            "test-collection",
            [memory_record1._id, memory_record2._id],
            with_embeddings=True,
        )
    )

    assert len(results) >= 2
    assert results[0]._id in [memory_record1._id, memory_record2._id]
    assert results[1]._id in [memory_record1._id, memory_record2._id]


@pytest.mark.asyncio
@pytest.mark.xfail(
    reason="Test failed due to known unreliable communications with Pinecone free tier"
)
async def test_remove(api_key, memory_record1):
    memory = PineconeMemoryStore(api_key, 2)

    await retry(lambda: memory.create_collection("test-collection"))
    await retry(lambda: memory.upsert("test-collection", memory_record1))
    await retry(lambda: memory.remove("test-collection", memory_record1._id))

    with pytest.raises(ServiceResourceNotFoundError):
        _ = await memory.get("test-collection", memory_record1._id, with_embedding=True)


@pytest.mark.asyncio
@pytest.mark.xfail(
    reason="Test failed due to known unreliable communications with Pinecone free tier"
)
async def test_remove_batch(api_key, memory_record1, memory_record2):
    memory = PineconeMemoryStore(api_key, 2)

    await retry(lambda: memory.create_collection("test-collection"))
    await retry(
        lambda: memory.upsert_batch("test-collection", [memory_record1, memory_record2])
    )
    await retry(
        lambda: memory.remove_batch(
            "test-collection", [memory_record1._id, memory_record2._id]
        )
    )

    with pytest.raises(ServiceResourceNotFoundError):
        _ = await memory.get("test-collection", memory_record1._id, with_embedding=True)

    with pytest.raises(ServiceResourceNotFoundError):
        _ = await memory.get("test-collection", memory_record2._id, with_embedding=True)


@pytest.mark.asyncio
@pytest.mark.xfail(
    reason="Test failed due to known unreliable communications with Pinecone free tier"
)
async def test_get_nearest_match(api_key, memory_record1, memory_record2):
    memory = PineconeMemoryStore(api_key, 2)

    await retry(lambda: memory.create_collection("test-collection"))
    await retry(
        lambda: memory.upsert_batch("test-collection", [memory_record1, memory_record2])
    )

    test_embedding = memory_record1.embedding
    test_embedding[0] = test_embedding[0] + 0.01

    result = await retry(
        lambda: memory.get_nearest_match(
            "test-collection",
            test_embedding,
            min_relevance_score=0.0,
            with_embedding=True,
        )
    )

    assert result is not None
    assert result[0]._id == memory_record1._id


@pytest.mark.asyncio
@pytest.mark.xfail(
    reason="Test failed due to known unreliable communications with Pinecone free tier"
)
async def test_get_nearest_matches(
    api_key, memory_record1, memory_record2, memory_record3
):
    memory = PineconeMemoryStore(api_key, 2)

    await retry(lambda: memory.create_collection("test-collection"))
    await retry(
        lambda: memory.upsert_batch(
            "test-collection", [memory_record1, memory_record2, memory_record3]
        )
    )

    test_embedding = memory_record2.embedding
    test_embedding[0] = test_embedding[0] + 0.025

    result = await retry(
        lambda: memory.get_nearest_matches(
            "test-collection",
            test_embedding,
            limit=2,
            min_relevance_score=0.0,
            with_embeddings=True,
        )
    )

    assert len(result) == 2
    assert result[0][0]._id in [memory_record3._id, memory_record2._id]
    assert result[1][0]._id in [memory_record3._id, memory_record2._id]
