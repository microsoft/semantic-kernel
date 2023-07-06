# Copyright (c) Microsoft. All rights reserved.

import numpy as np
import pytest

from semantic_kernel.connectors.memory.azure_cog_search.acs_memory_store import (
    CognitiveSearchMemoryStore,
)
from semantic_kernel.memory.memory_record import MemoryRecord

try:
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


def test_constructor():
    test_endpoint = "https://test-endpoint.search.windows.net"
    memory = CognitiveSearchMemoryStore(test_endpoint)
    assert memory._client is not None
