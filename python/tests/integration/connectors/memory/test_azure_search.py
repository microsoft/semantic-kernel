# Copyright (c) Microsoft. All rights reserved.

import time
from random import randint

import numpy as np
import pytest

from semantic_kernel.connectors.memory.azure_search.azure_search_memory_store import (
    AzureSearchMemoryStore,
)
from semantic_kernel.memory.memory_record import MemoryRecord

try:
    azure_search_installed = True
except ImportError:
    azure_search_installed = False

pytestmark = pytest.mark.skipif(
    not azure_search_installed, reason="Azure Search is not installed"
)


@pytest.fixture
def memory_store():
    yield AzureSearchMemoryStore(vector_size=4)


def test_constructor():
    test_endpoint = "https://test-endpoint.search.windows.net"
    memory = AzureSearchMemoryStore(test_endpoint)
    assert memory._search_index_client is not None


@pytest.mark.asyncio
async def test_collections(memory_store):
    n = randint(1000, 9999)
    collection = f"int-tests-{n}"
    await memory_store.create_collection_async(collection)
    time.sleep(1)
    try:
        assert await memory_store.does_collection_exist_async(collection)
    except:
        await memory_store.delete_collection_async(collection)
        raise

    await memory_store.delete_collection_async(collection)
    time.sleep(1)
    assert not await memory_store.does_collection_exist_async(collection)


@pytest.mark.asyncio
async def test_upsert(memory_store):
    n = randint(1000, 9999)
    collection = f"int-tests-{n}"
    await memory_store.create_collection_async(collection)
    time.sleep(1)
    try:
        assert await memory_store.does_collection_exist_async(collection)
        rec = MemoryRecord(
            is_reference=False,
            external_source_name=None,
            id=None,
            description="some description",
            text="some text",
            additional_metadata=None,
            embedding=np.array([0.2, 0.1, 0.2, 0.7]),
        )
        await memory_store.upsert_async(collection, rec)
        time.sleep(1)
        result = await memory_store.get_async(collection, rec._id)
        assert result._id == rec._id
        assert result._text == rec._text
    except:
        await memory_store.delete_collection_async(collection)
        raise

    await memory_store.delete_collection_async(collection)


@pytest.mark.asyncio
async def test_search(memory_store):
    n = randint(1000, 9999)
    collection = f"int-tests-{n}"
    await memory_store.create_collection_async(collection)
    time.sleep(1)
    try:
        assert await memory_store.does_collection_exist_async(collection)
        rec = MemoryRecord(
            is_reference=False,
            external_source_name=None,
            id=None,
            description="some description",
            text="some text",
            additional_metadata=None,
            embedding=np.array([0.1, 0.2, 0.3, 0.4]),
        )
        await memory_store.upsert_async(collection, rec)
        time.sleep(1)
        result = await memory_store.get_nearest_match_async(
            collection, np.array([0.1, 0.2, 0.3, 0.38])
        )
        assert result[0]._id == rec._id
    except:
        await memory_store.delete_collection_async(collection)
        raise

    await memory_store.delete_collection_async(collection)
