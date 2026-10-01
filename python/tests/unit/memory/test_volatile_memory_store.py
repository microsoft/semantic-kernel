# Copyright (c) Microsoft. All rights reserved.

import warnings

import numpy as np
import pytest

from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.volatile_memory_store import VolatileMemoryStore


@pytest.fixture
async def store() -> VolatileMemoryStore:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        memory_store = VolatileMemoryStore()
    await memory_store.create_collection("test")
    await memory_store.upsert("test", MemoryRecord.local_record("a", "text a", None, None, np.array([1.0, 0.0])))
    await memory_store.upsert("test", MemoryRecord.local_record("b", "text b", None, None, np.array([0.0, 1.0])))
    return memory_store


async def test_get_nearest_match_returns_tuple(store: VolatileMemoryStore):
    record, score = await store.get_nearest_match("test", np.array([1.0, 0.1]))

    assert record._id == "a"
    assert score == pytest.approx(0.995, abs=1e-3)


async def test_get_nearest_match_respects_min_relevance_score(store: VolatileMemoryStore):
    record, _ = await store.get_nearest_match("test", np.array([0.1, 1.0]), min_relevance_score=0.5)

    assert record._id == "b"
