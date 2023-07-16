# Copyright (c) Microsoft. All rights reserved.

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


def test_constructor():
    test_endpoint = "https://test-endpoint.search.windows.net"
    memory = AzureSearchMemoryStore(test_endpoint)
    assert memory._client is not None
