# Copyright (c) Microsoft. All rights reserved.

import numpy as np
import pytest

from semantic_kernel.connectors.memory.azure_cog_search.acs_memory_store import (
    CognitiveSearchMemoryStore,
)
from semantic_kernel.memory.memory_record import MemoryRecord

try:
    from azure.search.documents import SearchClient
    from azure.search.documents.indexes import SearchIndexClient

    az_search: SearchClient
    az_search_index: SearchIndexClient
    az_cog_search_installed = True
except ImportError:
    az_cog_search_installed = False

pytestmark = pytest.mark.skipif(
    not az_cog_search_installed, reason="Azure Cognitve Search is not installed"
)


@pytest.fixture
def memory_record1():
    return MemoryRecord(
        id="test_id1",
        text="sample text1",
        is_reference=False,
        embedding=np.array([0.5, 0.5]),
        description="description",
        external_source_name="external source",
        timestamp="timestamp",
    )


@pytest.fixture
def test_endpoint():
    return "https://fake.search.windows.net"


@pytest.fixture
def acs_key():
    return "fake_key"


@pytest.fixture
def credential():
    return None


def test_constructor(test_endpoint, credential, acs_key):
    memory = CognitiveSearchMemoryStore(
        test_endpoint, acs_search_key=acs_key, acs_credential=credential
    )
    assert memory is not None


@pytest.mark.asyncio
async def test_create_and_get_collection_async(test_endpoint, credential, acs_key):
    memory = CognitiveSearchMemoryStore(
        acs_endpoint=test_endpoint, acs_search_key=acs_key, acs_credential=credential
    )

    assert memory is not None

    index_name = "test_collection"
    vector_size = 512

    await memory.create_collection_async(
        collection_name=index_name, vector_size=vector_size
    )
    result = await memory.get_collection(collection_name=index_name)

    assert result is not None
