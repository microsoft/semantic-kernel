# Copyright (c) Microsoft. All rights reserved.

"""Extended Redis connector integration tests.

These supplement the single-record round-trip covered by
``test_vector_store.py`` and exercise the rest of the public surface
(`RedisStore.list_collection_names`, vector search with filters, batch
CRUD, `include_vectors`, manual index creation, and no-prefix mode)
to validate end-to-end compatibility with Redis and with Valkey +
valkey-search.

All tests require a running Redis/Valkey server reachable via
``REDIS_CONNECTION_STRING``.
"""

import asyncio
import contextlib
from dataclasses import dataclass, field
from typing import Annotated
from uuid import uuid4

import pytest

from semantic_kernel.connectors.redis import (
    RedisHashsetCollection,
    RedisJsonCollection,
    RedisStore,
)
from semantic_kernel.data.vector import VectorStoreField, vectorstoremodel
from semantic_kernel.exceptions import VectorStoreInitializationException

# Vector search was broken on main due to redisvl 0.5+ API change and a
# missing guard in the hashset deserializer.  Fixed by updating
# _inner_search to pass IndexSchema and guarding buffer_to_array.
# See: https://github.com/microsoft/semantic-kernel/issues/13896


@vectorstoremodel
@dataclass
class CoverageModel:
    """Shared record shape for all coverage tests."""

    vector: Annotated[
        list[float] | None,
        VectorStoreField(
            "vector",
            index_kind="hnsw",
            dimensions=5,
            distance_function="cosine_similarity",
            type="float",
        ),
    ] = None
    id: Annotated[str, VectorStoreField("key", type="str")] = field(default_factory=lambda: str(uuid4()))
    content: Annotated[str, VectorStoreField("data", type="str", is_full_text_indexed=True)] = "content"


def _records() -> list[CoverageModel]:
    return [
        CoverageModel(id="cov-1", content="alpha", vector=[0.1, 0.2, 0.3, 0.4, 0.5]),
        CoverageModel(id="cov-2", content="beta", vector=[0.2, 0.3, 0.4, 0.5, 0.6]),
        CoverageModel(id="cov-3", content="gamma", vector=[0.9, 0.8, 0.7, 0.6, 0.5]),
    ]


async def _collect(results):
    """Consume KernelSearchResults.results into a list."""
    return [r async for r in results.results]


@pytest.fixture
def collection_cls(request):
    """Parametrized fixture selecting the concrete collection class."""
    return request.param


@pytest.fixture
async def collection(collection_cls):
    """Yields a freshly-created collection; cleans the index up at teardown.

    Uses ``prefix_collection_name_to_key_names=True`` so each parametrized
    run has its own keyspace and hashset/json tests do not collide on
    raw keys.
    """
    name = f"sk_cov_{uuid4().hex[:8]}"
    try:
        col = collection_cls(
            record_type=CoverageModel,
            collection_name=name,
            prefix_collection_name_to_key_names=True,
        )
    except (VectorStoreInitializationException, ConnectionError) as exc:
        pytest.xfail(f"Failed to connect to store: {exc}")

    async with col:
        try:
            await col.ensure_collection_deleted()
            await col.ensure_collection_exists()
            yield col
        finally:
            with contextlib.suppress(Exception):
                await col.ensure_collection_deleted()


_COLLECTION_CLASSES = [
    pytest.param(RedisHashsetCollection, id="hashset"),
    pytest.param(RedisJsonCollection, id="json"),
]


@pytest.mark.parametrize("collection_cls", _COLLECTION_CLASSES, indirect=True)
class TestRedisCoverage:
    async def test_collection_exists_lifecycle(self, collection):
        """collection_exists tracks ensure_collection_exists / _deleted."""
        assert await collection.collection_exists() is True
        await collection.ensure_collection_deleted()
        assert await collection.collection_exists() is False
        await collection.ensure_collection_exists()
        assert await collection.collection_exists() is True

    async def test_list_collection_names_includes_created(self, collection):
        """RedisStore.list_collection_names surfaces the created index via FT._LIST."""
        try:
            store = RedisStore()
        except (VectorStoreInitializationException, ConnectionError) as exc:
            pytest.xfail(f"Failed to connect to store: {exc}")
        try:
            names = await store.list_collection_names()
            assert collection.collection_name in names
        finally:
            await store.redis_database.aclose()

    async def test_batch_upsert_get_delete(self, collection):
        """Multi-record upsert, get, and delete round-trip."""
        records = _records()
        await collection.upsert(records)

        fetched = await collection.get([r.id for r in records])
        assert fetched is not None
        assert {r.id for r in fetched} == {r.id for r in records}

        await collection.delete([r.id for r in records])
        after = await collection.get([r.id for r in records])
        assert not after

    async def test_get_include_vectors(self, collection):
        """get with include_vectors=True returns the vector, False hides it."""
        [first, *_] = _records()
        await collection.upsert([first])

        with_vec = await collection.get(first.id, include_vectors=True)
        without_vec = await collection.get(first.id, include_vectors=False)

        assert with_vec is not None
        assert without_vec is not None
        assert with_vec.vector is not None
        assert without_vec.vector is None

    async def test_vector_search_basic(self, collection):
        """FT.SEARCH with an HNSW query returns results ordered by distance."""
        records = _records()
        await collection.upsert(records)
        await asyncio.sleep(0.2)

        results = await _collect(await collection.search(vector=[0.1, 0.2, 0.3, 0.4, 0.5], top=3))
        assert len(results) == 3
        assert results[0].record.id == "cov-1"

    async def test_vector_search_top_skip(self, collection):
        """top/skip paging works end-to-end."""
        await collection.upsert(_records())
        await asyncio.sleep(0.2)

        page1 = await _collect(await collection.search(vector=[0.1, 0.2, 0.3, 0.4, 0.5], top=2, skip=0))
        page2 = await _collect(await collection.search(vector=[0.1, 0.2, 0.3, 0.4, 0.5], top=2, skip=2))
        assert len(page1) == 2
        assert len(page2) == 1
        seen = {r.record.id for r in page1} | {r.record.id for r in page2}
        assert seen == {"cov-1", "cov-2", "cov-3"}

    async def test_vector_search_with_tag_filter(self, collection):
        """Lambda filter on a text field is translated and honoured."""
        await collection.upsert(_records())
        await asyncio.sleep(0.2)

        results = await _collect(
            await collection.search(
                vector=[0.1, 0.2, 0.3, 0.4, 0.5],
                top=5,
                filter=lambda r: r.content == "beta",
            )
        )
        assert len(results) == 1
        assert results[0].record.id == "cov-2"

    async def test_vector_search_include_vectors(self, collection):
        """include_vectors toggles whether the vector is returned on search hits."""
        await collection.upsert(_records())
        await asyncio.sleep(0.2)

        with_vec = await _collect(
            await collection.search(vector=[0.1, 0.2, 0.3, 0.4, 0.5], top=1, include_vectors=True)
        )
        without_vec = await _collect(
            await collection.search(vector=[0.1, 0.2, 0.3, 0.4, 0.5], top=1, include_vectors=False)
        )
        assert with_vec[0].record.vector is not None
        assert without_vec[0].record.vector is None


class TestRedisCoverageNoPrefix:
    """prefix_collection_name_to_key_names=False should round-trip by raw key."""

    @pytest.mark.parametrize(
        "collection_cls",
        [
            pytest.param(RedisHashsetCollection, id="hashset"),
            pytest.param(RedisJsonCollection, id="json"),
        ],
    )
    async def test_upsert_get_delete_without_prefix(self, collection_cls):
        name = f"sk_cov_np_{uuid4().hex[:8]}"
        try:
            col = collection_cls(
                record_type=CoverageModel,
                collection_name=name,
                prefix_collection_name_to_key_names=False,
            )
        except (VectorStoreInitializationException, ConnectionError) as exc:
            pytest.xfail(f"Failed to connect to store: {exc}")

        async with col:
            await col.ensure_collection_deleted()
            await col.ensure_collection_exists()
            try:
                rec = CoverageModel(
                    id=f"np-{uuid4().hex[:6]}",
                    content="alpha",
                    vector=[0.1, 0.2, 0.3, 0.4, 0.5],
                )
                await col.upsert([rec])
                fetched = await col.get(rec.id)
                assert fetched is not None
                assert fetched.id == rec.id
                await col.delete(rec.id)
                assert not await col.get(rec.id)
            finally:
                await col.ensure_collection_deleted()


@pytest.mark.parametrize("collection_cls", _COLLECTION_CLASSES, indirect=True)
class TestRedisCoverageExtended:
    """Extra coverage for paths not exercised by TestRedisCoverage."""

    async def test_ensure_collection_exists_with_explicit_index(self, collection):
        """ensure_collection_exists(index_definition=..., fields=...) uses the provided override."""
        from redis.commands.search.field import TextField, VectorField
        from redis.commands.search.index_definition import IndexDefinition, IndexType

        await collection.ensure_collection_deleted()
        assert await collection.collection_exists() is False

        index_type = IndexType.JSON if isinstance(collection, RedisJsonCollection) else IndexType.HASH
        content_field = (
            TextField("$.content", as_name="content") if index_type == IndexType.JSON else TextField("content")
        )
        vector_field = (
            VectorField(
                "$.vector",
                "HNSW",
                {"TYPE": "FLOAT32", "DIM": 5, "DISTANCE_METRIC": "COSINE"},
                as_name="vector",
            )
            if index_type == IndexType.JSON
            else VectorField(
                "vector",
                "HNSW",
                {"TYPE": "FLOAT32", "DIM": 5, "DISTANCE_METRIC": "COSINE"},
            )
        )
        await collection.ensure_collection_exists(
            index_definition=IndexDefinition(prefix=[f"{collection.collection_name}:"], index_type=index_type),
            fields=[content_field, vector_field],
        )
        assert await collection.collection_exists() is True

    async def test_ensure_collection_exists_invalid_index_definition(self, collection):
        """Passing a non-IndexDefinition with fields should raise."""
        from semantic_kernel.exceptions import VectorStoreOperationException

        with pytest.raises(VectorStoreOperationException, match="Invalid index type supplied."):
            await collection.ensure_collection_exists(index_definition="not-an-IndexDefinition", fields=["content"])

    async def test_vector_search_not_equal_filter(self, collection):
        await collection.upsert(_records())
        await asyncio.sleep(0.2)
        results = await _collect(
            await collection.search(
                vector=[0.1, 0.2, 0.3, 0.4, 0.5],
                top=5,
                filter=lambda r: r.content != "alpha",
            )
        )
        ids = {r.record.id for r in results}
        assert ids == {"cov-2", "cov-3"}

    async def test_vector_search_and_filter(self, collection):
        await collection.upsert(_records())
        await asyncio.sleep(0.2)
        results = await _collect(
            await collection.search(
                vector=[0.1, 0.2, 0.3, 0.4, 0.5],
                top=5,
                filter=lambda r: (r.content != "alpha") and (r.content != "gamma"),
            )
        )
        assert {r.record.id for r in results} == {"cov-2"}

    async def test_vector_search_or_filter(self, collection):
        await collection.upsert(_records())
        await asyncio.sleep(0.2)
        results = await _collect(
            await collection.search(
                vector=[0.1, 0.2, 0.3, 0.4, 0.5],
                top=5,
                filter=lambda r: (r.content == "alpha") or (r.content == "gamma"),
            )
        )
        assert {r.record.id for r in results} == {"cov-1", "cov-3"}

    async def test_get_without_keys_not_implemented(self, collection):
        """get with no keys should raise NotImplementedError via the connector."""
        from semantic_kernel.data.vector import GetFilteredRecordOptions

        with pytest.raises(NotImplementedError):
            await collection._inner_get(keys=None, options=GetFilteredRecordOptions())
