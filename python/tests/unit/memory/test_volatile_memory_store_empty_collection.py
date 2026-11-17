# Copyright (c) Microsoft. All rights reserved.

import numpy as np

from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.volatile_memory_store import VolatileMemoryStore


async def test_get_nearest_matches_empty_collection_returns_empty_list():
    store = VolatileMemoryStore()
    await store.create_collection("c")

    result = await store.get_nearest_matches("c", np.array([1.0, 2.0]), limit=3)

    assert result == []


async def test_get_nearest_matches_after_removing_all_records_returns_empty_list():
    store = VolatileMemoryStore()
    await store.create_collection("c")
    record = MemoryRecord.local_record(
        id="a", text="t", description=None, additional_metadata=None, embedding=np.array([1.0, 0.0])
    )
    await store.upsert("c", record)
    await store.remove("c", "a")

    result = await store.get_nearest_matches("c", np.array([1.0, 0.0]), limit=1)

    assert result == []
