# Copyright (c) Microsoft. All rights reserved.

import time
from random import randint

import numpy as np
import pytest

from semantic_kernel.connectors.memory.azure_cognitive_search.azure_cognitive_search_memory_store import (
    AzureCognitiveSearchMemoryStore,
)
from semantic_kernel.memory.memory_record import MemoryRecord

try:
    azure_cognitive_search_installed = True
except ImportError:
    azure_cognitive_search_installed = False

pytestmark = pytest.mark.skipif(
    not azure_cognitive_search_installed,
    reason="Azure Cognitive Search is not installed",
)


@pytest.mark.asyncio
async def test_constructor():
    test_endpoint = "https://test-endpoint.search.windows.net"
    async with AzureCognitiveSearchMemoryStore(
        vector_size=4, search_endpoint=test_endpoint
    ) as memory_store:
        assert memory_store is not None
        assert memory_store._search_index_client is not None


@pytest.mark.asyncio
async def test_collections():
    collection = f"int-tests-{randint(1000, 9999)}"
    async with AzureCognitiveSearchMemoryStore(vector_size=4) as memory_store:
        await memory_store.create_collection_async(collection)
        time.sleep(1)
        try:
            assert await memory_store.does_collection_exist_async(collection)
        except:
            await memory_store.delete_collection_async(collection)
            raise

        many = await memory_store.get_collections_async()
        assert collection in many

        await memory_store.delete_collection_async(collection)
        time.sleep(1)
        assert not await memory_store.does_collection_exist_async(collection)


@pytest.mark.asyncio
async def test_upsert():
    collection = f"int-tests-{randint(1000, 9999)}"
    async with AzureCognitiveSearchMemoryStore(vector_size=4) as memory_store:
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
            id = await memory_store.upsert_async(collection, rec)
            time.sleep(1)

            many = await memory_store.get_batch_async(collection, [id])
            one = await memory_store.get_async(collection, id)

            assert many[0]._id == id
            assert one._id == id
            assert one._text == rec._text
        except:
            await memory_store.delete_collection_async(collection)
            raise

        await memory_store.delete_collection_async(collection)


@pytest.mark.asyncio
async def test_record_not_found():
    collection = f"int-tests-{randint(1000, 9999)}"
    async with AzureCognitiveSearchMemoryStore(vector_size=4) as memory_store:
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
            id = await memory_store.upsert_async(collection, rec)
        except:
            await memory_store.delete_collection_async(collection)
            raise

        try:
            await memory_store.remove_async(collection, id)
            time.sleep(1)

            # KeyError exception should occur
            await memory_store.get_async(collection, id)

            # Clean up and fail
            await memory_store.delete_collection_async(collection)
            assert False
        except KeyError:
            pass

        await memory_store.delete_collection_async(collection)


@pytest.mark.asyncio
async def test_search():
    collection = f"int-tests-{randint(1000, 9999)}"
    async with AzureCognitiveSearchMemoryStore(vector_size=4) as memory_store:
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
