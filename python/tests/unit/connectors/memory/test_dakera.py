# Copyright (c) Microsoft. All rights reserved.

"""Unit tests for DakeraMemoryStore.

Tests mock the aiohttp.ClientSession so no live Dakera instance is needed.
Run with: pytest tests/unit/connectors/memory/test_dakera.py -v
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from numpy import array

from semantic_kernel.connectors.memory_stores.dakera.dakera_memory_store import (
    DakeraMemoryStore,
    _DAKERA_ID_META_KEY,
    _payload_to_record,
    _record_to_payload,
)
from semantic_kernel.memory.memory_record import MemoryRecord


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def make_record(sk_id: str = "test-id", text: str = "hello world") -> MemoryRecord:
    """Build a minimal SK MemoryRecord for testing."""
    return MemoryRecord.local_record(
        id=sk_id,
        text=text,
        description="a test record",
        additional_metadata="extra",
        embedding=array([0.1, 0.2, 0.3]),
    )


def dakera_memory_item(
    dakera_uuid: str = "dakera-uuid-1",
    sk_id: str = "test-id",
    content: str = "hello world",
    score: float = 0.9,
) -> dict:
    """Simulate one item in a Dakera search response."""
    return {
        "memory": {
            "id": dakera_uuid,
            "content": content,
            "agent_id": "my-collection",
            "metadata": {
                _DAKERA_ID_META_KEY: sk_id,
                "_sk_description": "a test record",
                "_sk_is_reference": False,
                "_sk_external_source_name": "",
                "_sk_additional_metadata": "extra",
                "_sk_timestamp": "",
            },
        },
        "score": score,
    }


@pytest.fixture
def store():
    """Return a DakeraMemoryStore with a mock session."""
    s = DakeraMemoryStore(url="http://localhost:3300", api_key="demo", agent_id="test-agent")
    return s


# ---------------------------------------------------------------------------
# Helpers: _record_to_payload / _payload_to_record
# ---------------------------------------------------------------------------


def test_record_to_payload_round_trip():
    record = make_record()
    payload = _record_to_payload("col1", record)
    assert payload["agent_id"] == "col1"
    assert "hello world" in payload["content"]
    assert payload["metadata"][_DAKERA_ID_META_KEY] == "test-id"


def test_payload_to_record():
    item = dakera_memory_item()["memory"]
    record = _payload_to_record(item, with_embedding=False)
    assert record.id == "test-id"
    assert record.text == "hello world"
    assert record._key == "dakera-uuid-1"
    assert record._is_reference is False


# ---------------------------------------------------------------------------
# Collection management
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_collection(store):
    await store.create_collection("agents")
    assert "agents" in await store.get_collections()


@pytest.mark.asyncio
async def test_does_collection_exist_false(store):
    assert not await store.does_collection_exist("nonexistent")


@pytest.mark.asyncio
async def test_does_collection_exist_after_create(store):
    await store.create_collection("exists")
    assert await store.does_collection_exist("exists")


@pytest.mark.asyncio
async def test_delete_collection(store):
    await store.create_collection("to-delete")

    forget_response = {}

    async def mock_post(path, body):
        if path == "/v1/memory/forget":
            return forget_response
        pytest.fail(f"Unexpected POST to {path}")

    store._post = mock_post
    await store.delete_collection("to-delete")
    assert not await store.does_collection_exist("to-delete")


# ---------------------------------------------------------------------------
# Upsert
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upsert_returns_sk_id(store):
    record = make_record()
    store_response = {"memory": {"id": "dakera-abc-123", "content": "hello world"}}

    async def mock_post(path, body):
        assert path == "/v1/memory/store"
        assert body["agent_id"] == "my-collection"
        return store_response

    store._post = mock_post
    key = await store.upsert("my-collection", record)
    assert key == "test-id"  # SK key is the record's own id
    assert "my-collection" in store._known_collections


@pytest.mark.asyncio
async def test_upsert_batch(store):
    records = [make_record(sk_id=f"id-{i}") for i in range(3)]
    call_count = 0

    async def mock_post(path, body):
        nonlocal call_count
        call_count += 1
        return {"memory": {"id": f"dakera-{call_count}", "content": "x"}}

    store._post = mock_post
    keys = await store.upsert_batch("col", records)
    assert len(keys) == 3
    assert call_count == 3


# ---------------------------------------------------------------------------
# Get
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_found(store):
    search_response = {"memories": [dakera_memory_item(sk_id="test-id")]}

    async def mock_post(path, body):
        return search_response

    store._post = mock_post
    record = await store.get("my-collection", "test-id")
    assert record is not None
    assert record.id == "test-id"
    assert record.text == "hello world"


@pytest.mark.asyncio
async def test_get_not_found(store):
    # Returns results but none match the key
    search_response = {"memories": [dakera_memory_item(sk_id="other-id")]}

    async def mock_post(path, body):
        return search_response

    store._post = mock_post
    record = await store.get("my-collection", "missing-key")
    assert record is None


@pytest.mark.asyncio
async def test_get_batch(store):
    search_response = {
        "memories": [
            dakera_memory_item(sk_id="id-0"),
            dakera_memory_item(sk_id="id-1"),
        ]
    }

    async def mock_post(path, body):
        return search_response

    store._post = mock_post
    records = await store.get_batch("col", ["id-0", "id-1"])
    # Both keys happen to appear in the search results
    assert any(r.id == "id-0" for r in records)


# ---------------------------------------------------------------------------
# Remove
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_remove_existing(store):
    calls = []

    async def mock_post(path, body):
        calls.append((path, body))
        if path == "/v1/memory/search":
            return {"memories": [dakera_memory_item(dakera_uuid="dakera-uuid-1", sk_id="test-id")]}
        if path == "/v1/memory/forget":
            return {}
        pytest.fail(f"Unexpected path: {path}")

    store._post = mock_post
    await store.remove("col", "test-id")

    forget_call = next(c for c in calls if c[0] == "/v1/memory/forget")
    assert "dakera-uuid-1" in forget_call[1]["memory_ids"]


@pytest.mark.asyncio
async def test_remove_not_found_is_silent(store):
    async def mock_post(path, body):
        if path == "/v1/memory/search":
            return {"memories": []}  # nothing found
        pytest.fail(f"Should not reach {path}")

    store._post = mock_post
    # Should not raise
    await store.remove("col", "ghost-key")


@pytest.mark.asyncio
async def test_remove_batch(store):
    calls = []

    async def mock_post(path, body):
        calls.append((path, body))
        if path == "/v1/memory/search":
            return {
                "memories": [
                    dakera_memory_item(dakera_uuid="uuid-0", sk_id="id-0"),
                    dakera_memory_item(dakera_uuid="uuid-1", sk_id="id-1"),
                ]
            }
        if path == "/v1/memory/forget":
            return {}

    store._post = mock_post
    await store.remove_batch("col", ["id-0", "id-1"])
    forget_calls = [c for c in calls if c[0] == "/v1/memory/forget"]
    assert len(forget_calls) == 1  # single batched forget
    ids_sent = forget_calls[0][1]["memory_ids"]
    assert "uuid-0" in ids_sent or "uuid-1" in ids_sent


# ---------------------------------------------------------------------------
# get_nearest_matches / get_nearest_match
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_nearest_matches(store):
    search_response = {
        "memories": [
            {"memory": {"id": "d1", "content": "match 1", "agent_id": "col", "metadata": {_DAKERA_ID_META_KEY: "sk1"}}, "score": 0.95},
            {"memory": {"id": "d2", "content": "match 2", "agent_id": "col", "metadata": {_DAKERA_ID_META_KEY: "sk2"}}, "score": 0.80},
            {"memory": {"id": "d3", "content": "weak match", "agent_id": "col", "metadata": {_DAKERA_ID_META_KEY: "sk3"}}, "score": 0.30},
        ]
    }

    async def mock_post(path, body):
        return search_response

    store._post = mock_post
    results = await store.get_nearest_matches(
        collection_name="col",
        embedding=array([0.1, 0.2]),
        limit=2,
        min_relevance_score=0.5,
    )
    assert len(results) == 2
    assert results[0][1] == 0.95
    assert results[1][1] == 0.80


@pytest.mark.asyncio
async def test_get_nearest_match_returns_none_when_empty(store):
    async def mock_post(path, body):
        return {"memories": []}

    store._post = mock_post
    result = await store.get_nearest_match(
        collection_name="col",
        embedding=array([0.1]),
        min_relevance_score=0.9,
    )
    assert result is None


@pytest.mark.asyncio
async def test_get_nearest_match_single(store):
    search_response = {
        "memories": [
            {"memory": {"id": "d1", "content": "best match", "agent_id": "col", "metadata": {_DAKERA_ID_META_KEY: "sk1"}}, "score": 0.99},
        ]
    }

    async def mock_post(path, body):
        return search_response

    store._post = mock_post
    result = await store.get_nearest_match(
        collection_name="col",
        embedding=array([0.1]),
        min_relevance_score=0.5,
    )
    assert result is not None
    record, score = result
    assert score == 0.99
    assert record.text == "best match"


# ---------------------------------------------------------------------------
# search_text (convenience method)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_text(store):
    search_response = {
        "memories": [
            {"memory": {"id": "d1", "content": "result", "agent_id": "col", "metadata": {_DAKERA_ID_META_KEY: "sk1"}}, "score": 0.88},
        ]
    }

    async def mock_post(path, body):
        assert body["query"] == "my query"
        return search_response

    store._post = mock_post
    results = await store.search_text("col", "my query", top_k=5)
    assert len(results) == 1
    assert results[0][1] == 0.88


# ---------------------------------------------------------------------------
# HTTP error handling
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_raises_on_4xx(store):
    from semantic_kernel.exceptions import ServiceResponseException

    mock_resp = AsyncMock()
    mock_resp.status = 401
    mock_resp.text = AsyncMock(return_value="Unauthorized")
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_resp)
    store._session = mock_session

    with pytest.raises(ServiceResponseException, match="401"):
        await store._post("/v1/memory/store", {"content": "x", "agent_id": "y"})


# ---------------------------------------------------------------------------
# Context manager lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_context_manager_creates_and_closes_session():
    store = DakeraMemoryStore(url="http://localhost:3300")
    assert store._session is None

    with patch("aiohttp.ClientSession") as MockSession:
        instance = AsyncMock()
        MockSession.return_value = instance
        async with store:
            assert store._session is not None

    instance.close.assert_called_once()
