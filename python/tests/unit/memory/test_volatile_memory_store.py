# Copyright (c) Microsoft. All rights reserved.

import numpy as np

from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.volatile_memory_store import VolatileMemoryStore


async def test_get_nearest_matches_empty_collection():
    store = VolatileMemoryStore()
    await store.create_collection("test")
    result = await store.get_nearest_matches("test", np.array([1.0, 2.0]), limit=3)
    assert result == []


async def test_get_nearest_matches_missing_collection():
    store = VolatileMemoryStore()
    result = await store.get_nearest_matches("missing", np.array([1.0, 2.0]), limit=3)
    assert result == []


async def test_get_nearest_matches_with_records():
    store = VolatileMemoryStore()
    await store.create_collection("test")
    await store.upsert(
        "test",
        MemoryRecord(
            is_reference=False,
            external_source_name=None,
            id="first",
            description="first record",
            text="hello",
            additional_metadata=None,
            embedding=np.array([1.0, 0.0]),
        ),
    )
    result = await store.get_nearest_matches("test", np.array([1.0, 0.0]), limit=3)
    assert len(result) == 1
    assert result[0][0].id == "first"
