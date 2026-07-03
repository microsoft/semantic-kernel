# Copyright (c) Microsoft. All rights reserved.

"""Unit tests for DakeraMemoryStore.

The tests inject a mock ``AsyncDakeraClient`` so no live Dakera instance (and no
network) is required. Run with:
    pytest tests/unit/connectors/memory/test_dakera.py -v
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from numpy import array
from numpy.linalg import norm

from semantic_kernel.connectors.memory_stores.dakera.dakera_memory_store import (
    _SK_EMBEDDING,
    _SK_ID,
    DakeraMemoryStore,
    _record_to_metadata,
    _to_record,
)
from semantic_kernel.memory.memory_record import MemoryRecord

# ---------------------------------------------------------------------------
# Fixtures / helpers
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


def dakera_memory(
    dakera_uuid: str = "dakera-uuid-1",
    sk_id: str = "test-id",
    content: str = "hello world",
    score: float | None = None,
    embedding: list[float] | None = None,
):
    """Simulate a memory object returned by the Dakera SDK (attribute access)."""
    metadata = {
        _SK_ID: sk_id,
        "_sk_description": "a test record",
        "_sk_is_reference": False,
        "_sk_external_source_name": "",
        "_sk_additional_metadata": "extra",
        "_sk_timestamp": "",
    }
    if embedding is not None:
        metadata[_SK_EMBEDDING] = embedding
    obj = SimpleNamespace(id=dakera_uuid, content=content, metadata=metadata, importance=0.5)
    if score is not None:
        obj.score = score
    return obj


@pytest.fixture
def mock_client() -> AsyncMock:
    """An AsyncDakeraClient test double."""
    client = AsyncMock()
    client.store_memory = AsyncMock(return_value={"id": "dakera-uuid-1"})
    client.batch_recall = AsyncMock(return_value=SimpleNamespace(memories=[], total=0, filtered=0))
    client.batch_forget = AsyncMock(return_value=SimpleNamespace(deleted_count=0))
    client.forget = AsyncMock(return_value={})
    client.recall = AsyncMock(return_value=SimpleNamespace(memories=[]))
    client.close = AsyncMock()
    return client


@pytest.fixture
def store(mock_client: AsyncMock) -> DakeraMemoryStore:
    return DakeraMemoryStore(url="http://localhost:3000", api_key="dk-demo", client=mock_client)


def _recall_response(memories):
    return SimpleNamespace(memories=memories)


def _batch_response(memories):
    return SimpleNamespace(memories=memories, total=len(memories), filtered=len(memories))


# ---------------------------------------------------------------------------
# Conversion helpers — round-trip fidelity
# ---------------------------------------------------------------------------


def test_record_to_metadata_stores_embedding_and_fields():
    metadata = _record_to_metadata(make_record())
    assert metadata[_SK_ID] == "test-id"
    assert metadata["_sk_description"] == "a test record"
    assert metadata[_SK_EMBEDDING] == pytest.approx([0.1, 0.2, 0.3])


def test_text_round_trip_is_exact():
    """text must not be polluted with the description on read-back."""
    record = make_record(text="just the text")
    metadata = _record_to_metadata(record)
    # Dakera stores the raw text as `content`; description lives in metadata.
    reconstructed = _to_record("dakera-uuid-1", "just the text", metadata, with_embedding=False)
    assert reconstructed.text == "just the text"
    assert reconstructed.description == "a test record"
    assert reconstructed.id == "test-id"
    assert reconstructed._key == "dakera-uuid-1"


def test_to_record_hydrates_embedding_only_when_requested():
    metadata = _record_to_metadata(make_record())
    without = _to_record("d1", "hello world", metadata, with_embedding=False)
    assert without._embedding.size == 0

    with_emb = _to_record("d1", "hello world", metadata, with_embedding=True)
    assert with_emb._embedding.tolist() == pytest.approx([0.1, 0.2, 0.3])


# ---------------------------------------------------------------------------
# Collection management
# ---------------------------------------------------------------------------


async def test_create_and_exists(store: DakeraMemoryStore):
    assert not await store.does_collection_exist("agents")
    await store.create_collection("agents")
    assert "agents" in await store.get_collections()
    assert await store.does_collection_exist("agents")


async def test_delete_collection_uses_tag_filter(store: DakeraMemoryStore, mock_client: AsyncMock):
    await store.create_collection("to-delete")
    await store.delete_collection("to-delete")

    assert not await store.does_collection_exist("to-delete")
    mock_client.batch_forget.assert_awaited_once()
    request = mock_client.batch_forget.await_args.args[0]
    # Safety guard: a bulk delete must carry at least one filter predicate.
    assert request.agent_id == "to-delete"
    assert request.filter.tags == ["to-delete"]


# ---------------------------------------------------------------------------
# Upsert
# ---------------------------------------------------------------------------


async def test_upsert_returns_sk_id_and_keeps_dakera_key(store: DakeraMemoryStore, mock_client: AsyncMock):
    record = make_record()
    key = await store.upsert("my-collection", record)

    assert key == "test-id"  # SK id addresses the record
    assert record._key == "dakera-uuid-1"  # Dakera UUID retained internally
    assert "my-collection" in store._known_collections

    call = mock_client.store_memory.await_args.kwargs
    assert call["agent_id"] == "my-collection"
    assert call["content"] == "hello world"  # raw text, not "text | description"
    assert call["tags"] == ["my-collection", "sk"]
    assert call["metadata"][_SK_ID] == "test-id"


async def test_upsert_batch(store: DakeraMemoryStore, mock_client: AsyncMock):
    records = [make_record(sk_id=f"id-{i}") for i in range(3)]
    keys = await store.upsert_batch("col", records)
    assert keys == ["id-0", "id-1", "id-2"]
    assert mock_client.store_memory.await_count == 3


# ---------------------------------------------------------------------------
# Get
# ---------------------------------------------------------------------------


async def test_get_found(store: DakeraMemoryStore, mock_client: AsyncMock):
    mock_client.batch_recall.return_value = _batch_response([dakera_memory(sk_id="test-id")])
    record = await store.get("my-collection", "test-id")
    assert record is not None
    assert record.id == "test-id"
    assert record.text == "hello world"


async def test_get_not_found(store: DakeraMemoryStore, mock_client: AsyncMock):
    mock_client.batch_recall.return_value = _batch_response([dakera_memory(sk_id="other-id")])
    assert await store.get("my-collection", "missing-key") is None


async def test_get_batch(store: DakeraMemoryStore, mock_client: AsyncMock):
    mock_client.batch_recall.return_value = _batch_response([
        dakera_memory(dakera_uuid="d0", sk_id="id-0"),
        dakera_memory(dakera_uuid="d1", sk_id="id-1"),
    ])
    records = await store.get_batch("col", ["id-0", "id-1"])
    assert {r.id for r in records} == {"id-0", "id-1"}
    # A single collection scan resolves the whole batch.
    mock_client.batch_recall.assert_awaited_once()


# ---------------------------------------------------------------------------
# Remove
# ---------------------------------------------------------------------------


async def test_remove_existing(store: DakeraMemoryStore, mock_client: AsyncMock):
    mock_client.batch_recall.return_value = _batch_response([
        dakera_memory(dakera_uuid="dakera-uuid-1", sk_id="test-id")
    ])
    await store.remove("col", "test-id")
    mock_client.forget.assert_awaited_once_with("col", "dakera-uuid-1")


async def test_remove_not_found_is_silent(store: DakeraMemoryStore, mock_client: AsyncMock):
    mock_client.batch_recall.return_value = _batch_response([])
    await store.remove("col", "ghost-key")  # must not raise
    mock_client.forget.assert_not_awaited()


async def test_remove_batch_forgets_all_resolved_ids(store: DakeraMemoryStore, mock_client: AsyncMock):
    mock_client.batch_recall.return_value = _batch_response([
        dakera_memory(dakera_uuid="uuid-0", sk_id="id-0"),
        dakera_memory(dakera_uuid="uuid-1", sk_id="id-1"),
    ])
    await store.remove_batch("col", ["id-0", "id-1"])

    forgotten = {call.args[1] for call in mock_client.forget.await_args_list}
    # Both resolved UUIDs must be forgotten (regression guard).
    assert "uuid-0" in forgotten and "uuid-1" in forgotten


# ---------------------------------------------------------------------------
# get_nearest_matches / get_nearest_match — client-side cosine ranking
# ---------------------------------------------------------------------------


async def test_get_nearest_matches_ranks_by_query_embedding(store: DakeraMemoryStore, mock_client: AsyncMock):
    # Three stored vectors; the query is colinear with the middle one.
    mock_client.batch_recall.return_value = _batch_response([
        dakera_memory(dakera_uuid="d1", sk_id="sk1", content="up", embedding=[1.0, 0.0]),
        dakera_memory(dakera_uuid="d2", sk_id="sk2", content="diag", embedding=[1.0, 1.0]),
        dakera_memory(dakera_uuid="d3", sk_id="sk3", content="right", embedding=[0.0, 1.0]),
    ])
    results = await store.get_nearest_matches("col", embedding=array([1.0, 1.0]), limit=2)
    assert len(results) == 2
    # The colinear "diag" vector must rank first with score ~1.0.
    assert results[0][0].text == "diag"
    assert results[0][1] == pytest.approx(1.0)
    # Results are sorted descending by score.
    assert results[0][1] >= results[1][1]


async def test_get_nearest_matches_applies_min_relevance(store: DakeraMemoryStore, mock_client: AsyncMock):
    mock_client.batch_recall.return_value = _batch_response([
        dakera_memory(dakera_uuid="d1", sk_id="sk1", embedding=[1.0, 0.0]),
        dakera_memory(dakera_uuid="d2", sk_id="sk2", embedding=[0.0, 1.0]),
    ])
    # Query aligned with d1; d2 is orthogonal (score 0) and filtered out.
    results = await store.get_nearest_matches("col", embedding=array([1.0, 0.0]), limit=5, min_relevance_score=0.5)
    assert len(results) == 1
    assert results[0][0].id == "sk1"


async def test_get_nearest_matches_ignores_memories_without_embedding(store: DakeraMemoryStore, mock_client: AsyncMock):
    mock_client.batch_recall.return_value = _batch_response([dakera_memory(sk_id="sk1")])  # no embedding stored
    assert await store.get_nearest_matches("col", embedding=array([1.0, 0.0]), limit=5) == []


async def test_get_nearest_matches_hydrates_embeddings_when_requested(store: DakeraMemoryStore, mock_client: AsyncMock):
    mock_client.batch_recall.return_value = _batch_response([
        dakera_memory(dakera_uuid="d1", sk_id="sk1", embedding=[0.3, 0.4])
    ])
    results = await store.get_nearest_matches("col", embedding=array([0.3, 0.4]), limit=1, with_embeddings=True)
    record, score = results[0]
    assert record._embedding.tolist() == pytest.approx([0.3, 0.4])
    assert score == pytest.approx(float((array([0.3, 0.4]) @ array([0.3, 0.4])) / norm([0.3, 0.4]) ** 2))


async def test_get_nearest_match_returns_none_when_empty(store: DakeraMemoryStore, mock_client: AsyncMock):
    mock_client.batch_recall.return_value = _batch_response([])
    assert await store.get_nearest_match("col", embedding=array([0.1, 0.2]), min_relevance_score=0.9) is None


async def test_get_nearest_match_single(store: DakeraMemoryStore, mock_client: AsyncMock):
    mock_client.batch_recall.return_value = _batch_response([
        dakera_memory(dakera_uuid="d1", sk_id="sk1", content="best match", embedding=[1.0, 0.0])
    ])
    result = await store.get_nearest_match("col", embedding=array([1.0, 0.0]), min_relevance_score=0.5)
    assert result is not None
    record, score = result
    assert record.text == "best match"
    assert score == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# search_text — Dakera-native recall path
# ---------------------------------------------------------------------------


async def test_search_text_uses_recall(store: DakeraMemoryStore, mock_client: AsyncMock):
    mock_client.recall.return_value = _recall_response([
        dakera_memory(dakera_uuid="d1", sk_id="sk1", content="result", score=0.88)
    ])
    results = await store.search_text("col", "my query", top_k=5)

    mock_client.recall.assert_awaited_once_with(agent_id="col", query="my query", top_k=5)
    assert len(results) == 1
    assert results[0][0].text == "result"
    assert results[0][1] == pytest.approx(0.88)


async def test_search_text_applies_min_relevance(store: DakeraMemoryStore, mock_client: AsyncMock):
    mock_client.recall.return_value = _recall_response([
        dakera_memory(dakera_uuid="d1", sk_id="sk1", content="strong", score=0.9),
        dakera_memory(dakera_uuid="d2", sk_id="sk2", content="weak", score=0.1),
    ])
    results = await store.search_text("col", "q", top_k=5, min_relevance_score=0.5)
    assert [r[0].text for r in results] == ["strong"]


# ---------------------------------------------------------------------------
# Error handling / lifecycle
# ---------------------------------------------------------------------------


async def test_store_error_is_wrapped(store: DakeraMemoryStore, mock_client: AsyncMock):
    from dakera.exceptions import DakeraError

    from semantic_kernel.exceptions import ServiceResponseException

    mock_client.store_memory.side_effect = DakeraError("boom")
    with pytest.raises(ServiceResponseException):
        await store.upsert("col", make_record())


async def test_owned_client_is_closed_on_exit():
    from unittest.mock import patch

    with patch("semantic_kernel.connectors.memory_stores.dakera.dakera_memory_store.AsyncDakeraClient") as mock_ctor:
        instance = AsyncMock()
        mock_ctor.return_value = instance
        async with DakeraMemoryStore(url="http://localhost:3000") as s:
            assert s is not None
        instance.close.assert_awaited_once()


async def test_injected_client_is_not_closed(mock_client: AsyncMock):
    async with DakeraMemoryStore(client=mock_client):
        pass
    mock_client.close.assert_not_awaited()
