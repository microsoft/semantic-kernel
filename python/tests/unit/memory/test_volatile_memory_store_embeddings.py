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
    return memory_store


async def test_get_batch_without_embeddings(store: VolatileMemoryStore):
    results = await store.get_batch("test", ["a"], with_embeddings=False)

    assert results[0]._embedding is None
    # the stored record must keep its embedding
    assert store._store["test"]["a"]._embedding is not None


async def test_get_batch_with_embeddings(store: VolatileMemoryStore):
    results = await store.get_batch("test", ["a"], with_embeddings=True)

    assert results[0]._embedding is not None


async def test_get_nearest_matches_without_embeddings(store: VolatileMemoryStore):
    results = await store.get_nearest_matches("test", np.array([1.0, 0.0]), limit=1, with_embeddings=False)

    assert results[0][0]._embedding is None
    assert store._store["test"]["a"]._embedding is not None
    # a second query still works, so the stored embedding was not cleared
    again = await store.get_nearest_matches("test", np.array([1.0, 0.0]), limit=1, with_embeddings=True)
    assert again[0][0]._embedding is not None


async def test_get_nearest_matches_with_embeddings(store: VolatileMemoryStore):
    results = await store.get_nearest_matches("test", np.array([1.0, 0.0]), limit=1, with_embeddings=True)

    assert results[0][0]._embedding is not None
