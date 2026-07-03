# Copyright (c) Microsoft. All rights reserved.

"""DakeraMemoryStore — Semantic Kernel memory connector for Dakera.

`Dakera <https://dakera.ai>`_ is a self-hosted memory server that adds
persistent, decay-weighted vector recall across agent sessions: memories are
importance-scored and decay over time, so stale context stops competing with
fresh, relevant facts.

Run it locally with the public ``dakera-deploy`` docker-compose stack (the
server needs the object store the compose file provisions, so a bare
``docker run`` is not sufficient)::

    git clone https://github.com/dakera-ai/dakera-deploy
    cd dakera-deploy
    docker compose up -d          # serves the REST API on http://localhost:3000

Install the connector extra, which pulls the async Dakera SDK::

    pip install semantic-kernel[dakera]

The SK ``collection_name`` concept maps 1-to-1 to Dakera's ``agent_id``
namespace: each collection is a fully isolated memory silo inside the same
Dakera instance, so you can have as many logical collections as you like
without deploying more than once.

**Two retrieval paths**

``MemoryStoreBase.get_nearest_matches`` only receives a query *embedding*
(never the original query text), so this connector persists the SK-side
embedding alongside each memory and ranks candidates client-side with cosine
similarity. That keeps drop-in compatibility with ``SemanticTextMemory`` and
ranks in the caller's own embedding space.

For the richer, Dakera-native experience use :meth:`DakeraMemoryStore.search_text`,
which sends the raw query text to Dakera's ``recall`` endpoint and benefits
from server-side decay- and importance-weighted ranking.

Note: the legacy ``MemoryStoreBase`` API is deprecated upstream and will be
removed in a future SK release. New code should prefer the ``VectorStore`` API.
This connector targets the legacy API for compatibility with existing pipelines
that still use ``SemanticTextMemory``.
"""

import logging
import sys
from datetime import datetime
from typing import Any, Final

from dakera import AsyncDakeraClient
from dakera.exceptions import DakeraError, NotFoundError
from dakera.models import BatchForgetRequest, BatchMemoryFilter, BatchRecallRequest
from numpy import array, linalg, ndarray

from semantic_kernel.exceptions import ServiceResponseException
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase

if sys.version_info >= (3, 13):
    from warnings import deprecated
else:
    from typing_extensions import deprecated

logger: logging.Logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Metadata keys — SK record fields are round-tripped through Dakera's metadata
# blob so a stored record can be reconstructed losslessly on read.
# ---------------------------------------------------------------------------

_SK_ID: Final[str] = "_sk_id"
_SK_DESCRIPTION: Final[str] = "_sk_description"
_SK_IS_REFERENCE: Final[str] = "_sk_is_reference"
_SK_EXTERNAL_SOURCE: Final[str] = "_sk_external_source_name"
_SK_ADDITIONAL_METADATA: Final[str] = "_sk_additional_metadata"
_SK_TIMESTAMP: Final[str] = "_sk_timestamp"
_SK_EMBEDDING: Final[str] = "_sk_embedding"

# Tag applied to every memory this connector writes. It doubles as the
# collection marker (we also tag with the collection name) so a whole
# collection can be listed or purged with a single tag filter.
_SK_TAG: Final[str] = "sk"

# How many memories to page in when listing/scanning a collection. Dakera's
# batch-recall endpoint is filter-based (no query embedding required); this
# bounds the working set for client-side cosine ranking and id resolution.
_DEFAULT_FETCH_LIMIT: Final[int] = 1000

# Backwards-compatible alias kept for callers/tests that imported the old name.
_DAKERA_ID_META_KEY = _SK_ID


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------


def _record_to_metadata(record: MemoryRecord) -> dict[str, Any]:
    """Serialize the SK-specific fields of a MemoryRecord into a metadata dict.

    The embedding is stored too (as a plain float list) so that
    ``get_nearest_matches`` can rank client-side and ``with_embedding=True``
    reads can hydrate the original vector.
    """
    metadata: dict[str, Any] = {
        _SK_ID: record._id,
        _SK_DESCRIPTION: record._description or "",
        _SK_IS_REFERENCE: bool(record._is_reference),
        _SK_EXTERNAL_SOURCE: record._external_source_name or "",
        _SK_ADDITIONAL_METADATA: record._additional_metadata or "",
        _SK_TIMESTAMP: record._timestamp.isoformat() if record._timestamp else "",
    }
    embedding = record._embedding
    if embedding is not None and getattr(embedding, "size", 0):
        metadata[_SK_EMBEDDING] = array(embedding, dtype=float).tolist()
    return metadata


def _to_record(
    dakera_id: str,
    content: str,
    metadata: dict[str, Any] | None,
    with_embedding: bool,
) -> MemoryRecord:
    """Reconstruct a MemoryRecord from a Dakera memory (id + content + metadata).

    ``content`` maps straight back to ``MemoryRecord.text`` — the connector
    never packs the description into the content, so the round-trip is exact.
    """
    meta: dict[str, Any] = metadata or {}

    embedding: ndarray = array([])
    if with_embedding:
        raw = meta.get(_SK_EMBEDDING)
        if raw:
            embedding = array(raw, dtype=float)

    timestamp: datetime | None = None
    timestamp_str: str = meta.get(_SK_TIMESTAMP) or ""
    if timestamp_str:
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
        except ValueError:
            logger.debug("DakeraMemoryStore: could not parse timestamp %r", timestamp_str)

    return MemoryRecord(
        is_reference=bool(meta.get(_SK_IS_REFERENCE)),
        external_source_name=meta.get(_SK_EXTERNAL_SOURCE) or None,
        id=meta.get(_SK_ID) or dakera_id,
        description=meta.get(_SK_DESCRIPTION) or None,
        text=content,
        additional_metadata=meta.get(_SK_ADDITIONAL_METADATA) or None,
        embedding=embedding,
        key=dakera_id,  # Dakera's server-assigned UUID
        timestamp=timestamp,
    )


def _cosine_similarity(query: ndarray, vectors: ndarray) -> ndarray:
    """Cosine similarity between a query vector and a matrix of row vectors.

    Rows whose norm is zero (or that mismatch the query dimensionality) score
    ``-1.0`` so they sort last rather than raising.
    """
    query_norm = linalg.norm(query)
    col_norms = linalg.norm(vectors, axis=1)
    scores = array([-1.0] * vectors.shape[0])
    valid = (query_norm != 0) & (col_norms != 0)
    if valid.any():
        scores[valid] = vectors[valid].dot(query) / (col_norms[valid] * query_norm)
    return scores


# ---------------------------------------------------------------------------
# DakeraMemoryStore
# ---------------------------------------------------------------------------


@deprecated(
    "DakeraMemoryStore uses the deprecated MemoryStoreBase API which will be "
    "removed in a future SK version. Consider migrating to the VectorStore API."
)
class DakeraMemoryStore(MemoryStoreBase):
    """Semantic Kernel memory store backed by a Dakera server.

    This connector bridges SK's legacy ``MemoryStoreBase`` contract to Dakera's
    REST API (via the official async ``dakera`` SDK) so that any pipeline built
    on ``SemanticTextMemory`` can use Dakera as its backing store with no code
    changes outside the constructor.

    **Collection → agent_id mapping**

    An SK *collection* maps 1-to-1 to a Dakera ``agent_id`` — a fully isolated
    memory namespace. ``create_collection`` is a no-op registration (Dakera
    creates namespaces lazily on first write); ``delete_collection`` purges the
    namespace with a single tag-filtered batch forget.
    """

    def __init__(
        self,
        url: str = "http://localhost:3000",
        api_key: str | None = None,
        *,
        client: AsyncDakeraClient | None = None,
        fetch_limit: int = _DEFAULT_FETCH_LIMIT,
    ) -> None:
        """Initialize a new instance of the DakeraMemoryStore class.

        Args:
            url: Base URL of the Dakera server, e.g. ``http://localhost:3000``.
            api_key: Optional API key (looks like ``dk-...``). When ``None`` or
                empty, requests are sent without an ``Authorization`` header,
                which is fine for a Dakera instance deployed without auth.
            client: An existing :class:`~dakera.AsyncDakeraClient` to reuse. When
                provided, the store does not own its lifecycle and will not close
                it. When omitted, a client is created and owned by this instance.
            fetch_limit: Maximum number of memories paged in when listing or
                scanning a collection (client-side cosine ranking and id
                resolution). Defaults to ``1000``.
        """
        self._client: AsyncDakeraClient = client or AsyncDakeraClient(base_url=url, api_key=api_key or None)
        self._owns_client: bool = client is None
        self._fetch_limit: int = fetch_limit

        # Dakera has no list-all-agents endpoint, so we track collections that
        # have been created or written to during this store's lifetime to
        # answer get_collections()/does_collection_exist() without a round-trip.
        self._known_collections: set[str] = set()

    # ------------------------------------------------------------------
    # Context manager / lifecycle
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "DakeraMemoryStore":
        """Enter the async context, returning this store."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Exit the async context, closing an owned client."""
        await self.close()

    async def close(self) -> None:
        """Close the underlying Dakera client (only if this store created it)."""
        if self._owns_client:
            await self._client.close()

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    async def create_collection(self, collection_name: str) -> None:
        """Register a collection name locally.

        Dakera creates namespaces lazily on the first write, so this only
        records the name for ``get_collections``/``does_collection_exist``.
        """
        self._known_collections.add(collection_name)
        logger.debug("DakeraMemoryStore: registered collection '%s'", collection_name)

    async def get_collections(self) -> list[str]:
        """Return the collection names seen during this store's lifetime.

        Dakera does not expose a list-all-agents endpoint, so this returns the
        in-process set of collections created or written to since the store was
        instantiated. For a persistent view across restarts, call
        ``create_collection`` for each known collection at startup.
        """
        return list(self._known_collections)

    async def delete_collection(self, collection_name: str) -> None:
        """Delete every memory this connector stored in the collection.

        Issues a single tag-filtered batch forget (``tags=[collection_name]``),
        which satisfies Dakera's safety guard that a bulk delete must carry at
        least one filter predicate.
        """
        request = BatchForgetRequest(
            agent_id=collection_name,
            filter=BatchMemoryFilter(tags=[collection_name]),
        )
        try:
            await self._client.batch_forget(request)
        except NotFoundError:
            # Nothing to delete — treat as success.
            pass
        except DakeraError as exc:
            raise ServiceResponseException(f"Dakera batch_forget failed for '{collection_name}': {exc}") from exc
        self._known_collections.discard(collection_name)
        logger.debug("DakeraMemoryStore: deleted collection '%s'", collection_name)

    async def does_collection_exist(self, collection_name: str) -> bool:
        """Return True if this collection has been seen during the store's lifetime."""
        return collection_name in self._known_collections

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    async def upsert(self, collection_name: str, record: MemoryRecord) -> str:
        """Store a single MemoryRecord in Dakera.

        Returns:
            str: The SK record id — the key that addresses this record in
            subsequent ``get``/``remove`` calls. (Dakera's own server-assigned
            UUID is retained on ``record._key`` for internal use.)
        """
        content = record._text or record._description or record._id
        try:
            memory = await self._client.store_memory(
                agent_id=collection_name,
                content=content,
                metadata=_record_to_metadata(record),
                tags=[collection_name, _SK_TAG],
            )
        except DakeraError as exc:
            raise ServiceResponseException(f"Dakera store_memory failed: {exc}") from exc

        dakera_id = memory.get("id") if isinstance(memory, dict) else None
        if not dakera_id:
            raise ServiceResponseException(f"Dakera did not return a memory id after store. Response: {memory!r}")

        record._key = dakera_id
        self._known_collections.add(collection_name)
        return record._id

    async def upsert_batch(self, collection_name: str, records: list[MemoryRecord]) -> list[str]:
        """Store multiple MemoryRecords, returning their SK ids in order."""
        import asyncio

        return list(await asyncio.gather(*(self.upsert(collection_name, r) for r in records)))

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    async def get(self, collection_name: str, key: str, with_embedding: bool = False) -> MemoryRecord | None:
        """Retrieve a single MemoryRecord by its SK id.

        Resolves the SK id against the collection's stored ``_sk_id`` metadata
        (Dakera addresses records by its own UUID, not the SK id).

        Returns:
            The MemoryRecord if found, otherwise ``None``.
        """
        for memory in await self._list_collection(collection_name):
            meta = memory.metadata or {}
            if meta.get(_SK_ID) == key:
                return _to_record(memory.id, memory.content, meta, with_embedding)
        return None

    async def get_batch(
        self,
        collection_name: str,
        keys: list[str],
        with_embeddings: bool = False,
    ) -> list[MemoryRecord]:
        """Retrieve multiple MemoryRecords by their SK ids (single collection scan)."""
        wanted = set(keys)
        results: list[MemoryRecord] = []
        for memory in await self._list_collection(collection_name):
            meta = memory.metadata or {}
            sk_id = meta.get(_SK_ID)
            if sk_id in wanted:
                results.append(_to_record(memory.id, memory.content, meta, with_embeddings))
        return results

    # ------------------------------------------------------------------
    # Delete operations
    # ------------------------------------------------------------------

    async def remove(self, collection_name: str, key: str) -> None:
        """Remove a single MemoryRecord by its SK id (no-op if not found)."""
        dakera_id = await self._resolve_dakera_id(collection_name, key)
        if dakera_id is None:
            logger.warning(
                "DakeraMemoryStore.remove: key '%s' not found in collection '%s'; skipping.",
                key,
                collection_name,
            )
            return
        await self._forget(collection_name, dakera_id)

    async def remove_batch(self, collection_name: str, keys: list[str]) -> None:
        """Remove multiple MemoryRecords by their SK ids (single collection scan)."""
        import asyncio

        wanted = set(keys)
        dakera_ids = [
            memory.id
            for memory in await self._list_collection(collection_name)
            if (memory.metadata or {}).get(_SK_ID) in wanted
        ]
        if not dakera_ids:
            return
        await asyncio.gather(*(self._forget(collection_name, did) for did in dakera_ids))

    # ------------------------------------------------------------------
    # Similarity search
    # ------------------------------------------------------------------

    async def get_nearest_matches(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float = 0.0,
        with_embeddings: bool = False,
    ) -> list[tuple[MemoryRecord, float]]:
        """Find the nearest memories to ``embedding`` by cosine similarity.

        ``MemoryStoreBase`` passes only the query embedding (not the query
        text), so results are ranked client-side against the embeddings this
        connector persisted at write time — i.e. in the caller's own embedding
        space. For Dakera's native, server-side decay-weighted ranking over a
        text query, use :meth:`search_text` instead.

        Args:
            collection_name: The Dakera ``agent_id`` namespace to search.
            embedding: The query embedding.
            limit: Maximum number of matches to return.
            min_relevance_score: Minimum cosine score (inclusive) to keep.
            with_embeddings: When True, hydrate each result's stored embedding.

        Returns:
            ``(MemoryRecord, score)`` tuples sorted by score descending.
        """
        memories = await self._list_collection(collection_name)

        scored: list[tuple[Any, list[float]]] = []
        for memory in memories:
            raw = (memory.metadata or {}).get(_SK_EMBEDDING)
            if raw:
                scored.append((memory, raw))
        if not scored:
            return []

        query = array(embedding, dtype=float)
        matrix = array([vec for _memory, vec in scored], dtype=float)
        similarities = _cosine_similarity(query, matrix)

        ranked = sorted(
            zip((memory for memory, _vec in scored), similarities),
            key=lambda pair: pair[1],
            reverse=True,
        )

        output: list[tuple[MemoryRecord, float]] = []
        for memory, score in ranked:
            score = float(score)
            if score < min_relevance_score:
                continue
            output.append((_to_record(memory.id, memory.content, memory.metadata, with_embeddings), score))
            if len(output) >= limit:
                break
        return output

    async def get_nearest_match(
        self,
        collection_name: str,
        embedding: ndarray,
        min_relevance_score: float = 0.0,
        with_embedding: bool = False,
    ) -> tuple[MemoryRecord, float] | None:
        """Find the single nearest memory, or ``None`` if none meet the threshold."""
        results = await self.get_nearest_matches(
            collection_name=collection_name,
            embedding=embedding,
            limit=1,
            min_relevance_score=min_relevance_score,
            with_embeddings=with_embedding,
        )
        return results[0] if results else None

    # ------------------------------------------------------------------
    # Dakera-native text search (extends the base contract)
    # ------------------------------------------------------------------

    async def search_text(
        self,
        collection_name: str,
        query: str,
        top_k: int = 5,
        min_relevance_score: float = 0.0,
    ) -> list[tuple[MemoryRecord, float]]:
        """Search Dakera with a raw text query (recommended for Dakera-native apps).

        Unlike :meth:`get_nearest_matches`, this sends the query text straight
        to Dakera's ``recall`` endpoint, so ranking uses Dakera's server-side
        decay- and importance-weighted scoring rather than a client-side
        cosine over SK embeddings.

        Args:
            collection_name: The Dakera ``agent_id`` namespace to search.
            query: Plain-text search query.
            top_k: Number of results to return.
            min_relevance_score: Minimum relevance score (inclusive) to keep.

        Returns:
            ``(MemoryRecord, score)`` tuples sorted by score descending.
        """
        try:
            response = await self._client.recall(agent_id=collection_name, query=query, top_k=top_k)
        except NotFoundError:
            return []
        except DakeraError as exc:
            raise ServiceResponseException(f"Dakera recall failed for '{collection_name}': {exc}") from exc

        results: list[tuple[MemoryRecord, float]] = []
        for memory in response.memories:
            score = float(memory.score)
            if score < min_relevance_score:
                continue
            results.append((_to_record(memory.id, memory.content, memory.metadata, False), score))
            if len(results) >= top_k:
                break
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _list_collection(self, collection_name: str) -> list[Any]:
        """List the memories this connector stored in a collection.

        Uses Dakera's filter-based batch recall (``tags=[collection_name]``),
        which needs no query embedding and returns deterministic results.
        """
        request = BatchRecallRequest(
            agent_id=collection_name,
            filter=BatchMemoryFilter(tags=[collection_name]),
            limit=self._fetch_limit,
        )
        try:
            response = await self._client.batch_recall(request)
        except NotFoundError:
            return []
        except DakeraError as exc:
            raise ServiceResponseException(f"Dakera batch_recall failed for '{collection_name}': {exc}") from exc
        return list(response.memories)

    async def _resolve_dakera_id(self, collection_name: str, sk_key: str) -> str | None:
        """Return the Dakera UUID for an SK record id, or ``None`` if absent."""
        for memory in await self._list_collection(collection_name):
            if (memory.metadata or {}).get(_SK_ID) == sk_key:
                return memory.id
        return None

    async def _forget(self, collection_name: str, dakera_id: str) -> None:
        try:
            await self._client.forget(collection_name, dakera_id)
        except NotFoundError:
            pass
        except DakeraError as exc:
            raise ServiceResponseException(f"Dakera forget failed for '{dakera_id}': {exc}") from exc
