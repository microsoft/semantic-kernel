# Copyright (c) Microsoft. All rights reserved.

import numpy as np
import pytest

from pytest import raises

from semantic_kernel.exceptions import ServiceResourceNotFoundError
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.volatile_memory_store import VolatileMemoryStore


@pytest.mark.asyncio
async def test_get_nearest_match_awaits_and_returns_tuple() -> None:
    """get_nearest_match must await get_nearest_matches (issue #14521)."""
    store = VolatileMemoryStore()
    await store.create_collection("c")
    await store.upsert(
        "c",
        MemoryRecord.local_record(
            "id1",
            "text",
            "desc",
            None,
            np.array([1.0, 0.0], dtype=float),
        ),
    )
    match = await store.get_nearest_match("c", np.array([1.0, 0.0], dtype=float))
    assert isinstance(match, tuple)
    assert len(match) == 2
    record, score = match
    assert record.id == "id1"
    assert score >= 0.0


@pytest.mark.asyncio
async def test_get_nearest_match_raises_when_no_match() -> None:
    store = VolatileMemoryStore()
    await store.create_collection("c")
    await store.upsert(
        "c",
        MemoryRecord.local_record(
            "id1",
            "text",
            "desc",
            None,
            np.array([1.0, 0.0], dtype=float),
        ),
    )
    with raises(ServiceResourceNotFoundError, match="No match found"):
        await store.get_nearest_match(
            "c",
            np.array([1.0, 0.0], dtype=float),
            min_relevance_score=1.1,
        )
