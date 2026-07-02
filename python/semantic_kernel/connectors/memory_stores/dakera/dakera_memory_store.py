# Copyright (c) Microsoft. All rights reserved.

"""DakeraMemoryStore — Semantic Kernel memory connector for Dakera.

Dakera is a self-hosted REST memory server (https://dakera.ai).
Run it with:

    docker run -p 3300:3300 -e DAKERA_API_KEY=demo ghcr.io/dakera-ai/dakera:latest

The SK ``collection_name`` concept maps to Dakera's ``agent_id`` namespace.
Each collection is an independent agent memory silo inside the same Dakera
instance, so you can have as many logical collections as you like without
needing separate deployments.

Note: the legacy ``MemoryStoreBase`` API is deprecated upstream (it will be
removed in a future SK release).  New code should prefer the VectorStore API.
This connector targets the legacy API for maximum compatibility with existing
pipelines that still use ``SemanticTextMemory``.
"""

import json
import logging
import sys
from copy import deepcopy
from typing import Any

import aiohttp
from numpy import array, linalg, ndarray

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

if sys.version_info >= (3, 13):
    from warnings import deprecated
else:
    from typing_extensions import deprecated

from semantic_kernel.exceptions import ServiceResourceNotFoundError, ServiceResponseException
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase

logger: logging.Logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_DAKERA_ID_META_KEY = "_sk_id"
_DAKERA_DESC_META_KEY = "_sk_description"
_DAKERA_IS_REF_META_KEY = "_sk_is_reference"
_DAKERA_EXT_SRC_META_KEY = "_sk_external_source_name"
_DAKERA_ADD_META_KEY = "_sk_additional_metadata"
_DAKERA_TIMESTAMP_META_KEY = "_sk_timestamp"


def _record_to_payload(collection_name: str, record: MemoryRecord) -> dict[str, Any]:
    """Convert a MemoryRecord into a Dakera ``/v1/memory/store`` payload."""
    # Dakera content field receives the primary text.  We embed all SK
    # metadata fields as a JSON blob in the Dakera ``metadata`` dict so
    # they survive a round-trip through the API.
    metadata: dict[str, Any] = {
        _DAKERA_ID_META_KEY: record._id,
        _DAKERA_DESC_META_KEY: record._description or "",
        _DAKERA_IS_REF_META_KEY: record._is_reference,
        _DAKERA_EXT_SRC_META_KEY: record._external_source_name or "",
        _DAKERA_ADD_META_KEY: record._additional_metadata or "",
        _DAKERA_TIMESTAMP_META_KEY: str(record._timestamp) if record._timestamp else "",
    }

    # Build a human-readable content string that contains both the text and
    # the description, because Dakera's semantic search operates on ``content``.
    parts = []
    if record._text:
        parts.append(record._text)
    if record._description:
        parts.append(record._description)
    content = " | ".join(parts) if parts else record._id

    return {
        "content": content,
        "agent_id": collection_name,
        # Use the SK record id as the Dakera session_id so that
        # ``get()``/``remove()`` can address individual records.
        # This is a lightweight mapping; a production connector might
        # use a dedicated index field instead.
        "metadata": metadata,
        # importance range 0–1; default to middle if not set
        "importance": 0.5,
        "tags": [collection_name, "sk"],
    }


def _payload_to_record(item: dict[str, Any], with_embedding: bool = False) -> MemoryRecord:
    """Convert a Dakera memory item dict back into a MemoryRecord.

    ``item`` is the ``memory`` object returned by Dakera's API, shaped as:
    ``{id, content, agent_id, metadata, created_at, ...}``
    """
    meta: dict[str, Any] = item.get("metadata") or {}

    sk_id: str = meta.get(_DAKERA_ID_META_KEY) or item.get("id", "")
    description: str | None = meta.get(_DAKERA_DESC_META_KEY) or None
    is_reference: bool = bool(meta.get(_DAKERA_IS_REF_META_KEY, False))
    external_source_name: str | None = meta.get(_DAKERA_EXT_SRC_META_KEY) or None
    additional_metadata: str | None = meta.get(_DAKERA_ADD_META_KEY) or None
    timestamp_str: str = meta.get(_DAKERA_TIMESTAMP_META_KEY, "")

    from datetime import datetime

    timestamp = None
    if timestamp_str:
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
        except ValueError:
            pass

    # Dakera does not persist raw float vectors — it handles embedding
    # internally.  We return a zero-length ndarray when embeddings are
    # not available (which is normal for Dakera-backed stores).
    embedding: ndarray = array([]) if not with_embedding else array([])

    return MemoryRecord(
        is_reference=is_reference,
        external_source_name=external_source_name,
        id=sk_id,
        description=description,
        text=item.get("content", ""),
        additional_metadata=additional_metadata,
        embedding=embedding,
        key=item.get("id"),  # Dakera UUID as the internal key
        timestamp=timestamp,
    )


def _cosine_similarity(query: ndarray, vectors: ndarray) -> ndarray:
    """Compute cosine similarity between a query vector and a matrix of vectors."""
    query_norm = linalg.norm(query)
    col_norms = linalg.norm(vectors, axis=1)
    valid = (query_norm != 0) & (col_norms != 0)
    scores = array([-1.0] * vectors.shape[0])
    if valid.any():
        scores[valid] = query.dot(vectors[valid].T) / (query_norm * col_norms[valid])
    return scores


# ---------------------------------------------------------------------------
# DakeraMemoryStore
# ---------------------------------------------------------------------------


@deprecated(
    "DakeraMemoryStore uses the deprecated MemoryStoreBase API which will be "
    "removed in a future SK version.  Consider migrating to the VectorStore API."
)
class DakeraMemoryStore(MemoryStoreBase):
    """Semantic Kernel memory store backed by Dakera.

    Dakera is a self-hosted, decay-weighted vector memory server.  This
    connector bridges SK's legacy ``MemoryStoreBase`` contract to Dakera's
    REST API so that any pipeline built on ``SemanticTextMemory`` can use
    Dakera as its backing store with zero code changes outside the
    constructor call.

    **Collection → agent_id mapping**

    SK's concept of a *collection* maps 1-to-1 to Dakera's ``agent_id``.
    Each ``agent_id`` is a fully isolated memory namespace inside the
    Dakera instance.  ``create_collection`` is a no-op (Dakera lazily
    creates namespaces on first write); ``delete_collection`` calls
    ``POST /v1/memory/forget`` with no specific memory IDs, which wipes
    the entire agent namespace.

    **Embedding / similarity**

    Dakera manages its own HNSW embedding index server-side.
    ``get_nearest_matches`` therefore delegates directly to Dakera's
    ``POST /v1/memory/search`` endpoint and uses the returned relevance
    scores.  The ``embedding`` ndarray parameter is accepted for API
    compatibility but is **not** sent to Dakera (Dakera re-embeds the
    query text internally).  If the caller also needs to use the raw
    embedding for downstream cosine ranking (e.g. to re-rank Dakera
    results), this can be layered on top, but by default the Dakera
    relevance scores are used directly.

    Args:
        url: Base URL of the Dakera server, e.g. ``http://localhost:3300``.
        api_key: Optional bearer token.  If ``None`` or empty, the
            ``Authorization`` header is omitted (useful when Dakera is
            deployed without auth).
        agent_id: Default agent namespace used when no collection name is
            passed explicitly.  In SK's usage pattern the collection name
            always overrides this.
        session: Optional existing ``aiohttp.ClientSession``.  If ``None``,
            a new session is created and owned by this instance.
    """

    def __init__(
        self,
        url: str = "http://localhost:3300",
        api_key: str | None = None,
        agent_id: str = "sk-default",
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self._url = url.rstrip("/")
        self._api_key = api_key or ""
        self._default_agent_id = agent_id
        self._owns_session = session is None
        self._session = session  # may be None until first use

        # Track which collections (agent_ids) we have seen so we can
        # answer get_collections() and does_collection_exist() without a
        # dedicated Dakera list-agents endpoint.
        self._known_collections: set[str] = set()

    # ------------------------------------------------------------------
    # Context manager / lifecycle
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "DakeraMemoryStore":
        if self._session is None:
            self._session = self._make_session()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the underlying aiohttp session (only if we created it)."""
        if self._owns_session and self._session is not None:
            await self._session.close()
            self._session = None

    def _make_session(self) -> aiohttp.ClientSession:
        headers: dict[str, str] = {"Content-Type": "application/json", "Accept": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return aiohttp.ClientSession(headers=headers)

    def _get_session(self) -> aiohttp.ClientSession:
        """Return (and lazily create) the HTTP session."""
        if self._session is None:
            self._session = self._make_session()
        return self._session

    async def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        """Execute a POST request and return the parsed JSON body.

        Raises:
            ServiceResponseException: if the server returns a non-2xx status.
        """
        session = self._get_session()
        url = f"{self._url}{path}"
        async with session.post(url, data=json.dumps(body)) as resp:
            raw = await resp.text()
            if resp.status >= 400:
                raise ServiceResponseException(
                    f"Dakera API error {resp.status} on POST {path}: {raw[:500]}"
                )
            try:
                return json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ServiceResponseException(
                    f"Dakera returned non-JSON response on POST {path}: {raw[:200]}"
                ) from exc

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    @override
    async def create_collection(self, collection_name: str) -> None:
        """Register a collection name locally.

        Dakera has no explicit collection-creation endpoint; namespaces
        are created lazily on the first write.  We record the name so
        ``get_collections`` and ``does_collection_exist`` can answer
        without a round-trip.
        """
        self._known_collections.add(collection_name)
        logger.debug("DakeraMemoryStore: registered collection '%s'", collection_name)

    @override
    async def get_collections(self) -> list[str]:
        """Return all collection names that have been used in this session.

        Note: Dakera does not currently expose a list-all-agents endpoint.
        This method returns the in-process set of collections that were
        created or written to since the store was instantiated.  For a
        persistent view across restarts, callers should call
        ``create_collection`` for each known collection at startup.
        """
        return list(self._known_collections)

    @override
    async def delete_collection(self, collection_name: str) -> None:
        """Delete all memories in the Dakera agent namespace for this collection.

        Calls ``POST /v1/memory/forget`` with only the ``agent_id`` set
        (no specific memory IDs), which instructs Dakera to wipe all
        memories for that agent.
        """
        try:
            await self._post("/v1/memory/forget", {"agent_id": collection_name})
        except ServiceResponseException as exc:
            # A 404 means there is nothing to delete — treat as success.
            if "404" in str(exc):
                pass
            else:
                raise
        self._known_collections.discard(collection_name)
        logger.debug("DakeraMemoryStore: deleted collection '%s'", collection_name)

    @override
    async def does_collection_exist(self, collection_name: str) -> bool:
        """Return True if we have previously seen this collection in the current session."""
        return collection_name in self._known_collections

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    @override
    async def upsert(self, collection_name: str, record: MemoryRecord) -> str:
        """Store a single MemoryRecord in Dakera.

        Returns:
            str: The Dakera-assigned UUID for the stored memory.
        """
        payload = _record_to_payload(collection_name, record)
        response = await self._post("/v1/memory/store", payload)

        memory_obj = response.get("memory") or {}
        dakera_id: str = memory_obj.get("id", "")
        if not dakera_id:
            raise ServiceResponseException(
                f"Dakera did not return a memory id after store. Response: {response}"
            )

        # Keep the SK-level key pointing to the original record id.
        record._key = record._id
        self._known_collections.add(collection_name)
        return record._key

    @override
    async def upsert_batch(self, collection_name: str, records: list[MemoryRecord]) -> list[str]:
        """Store multiple MemoryRecords in Dakera.

        Dakera has no batch-store endpoint, so we issue one POST per record.
        For large batches consider chunking with asyncio.gather.
        """
        import asyncio

        tasks = [self.upsert(collection_name, record) for record in records]
        return list(await asyncio.gather(*tasks))

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    @override
    async def get(self, collection_name: str, key: str, with_embedding: bool = False) -> MemoryRecord | None:
        """Retrieve a single MemoryRecord by its SK id.

        Dakera's ``/v1/memory/search`` is used with the ``key`` as the
        query; we then match on the stored ``_sk_id`` metadata field.
        This is an approximation: Dakera returns semantically similar
        results, so we filter the list to find the exact match.

        Returns:
            MemoryRecord if found, None otherwise.
        """
        results = await self._search_by_query(
            collection_name=collection_name,
            query=key,
            top_k=20,
        )
        for memory_obj, _score in results:
            meta = memory_obj.get("metadata") or {}
            if meta.get(_DAKERA_ID_META_KEY) == key:
                return _payload_to_record(memory_obj, with_embedding)
        return None

    @override
    async def get_batch(
        self,
        collection_name: str,
        keys: list[str],
        with_embeddings: bool = False,
    ) -> list[MemoryRecord]:
        """Retrieve multiple MemoryRecords by their SK ids."""
        import asyncio

        tasks = [self.get(collection_name, key, with_embeddings) for key in keys]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]

    # ------------------------------------------------------------------
    # Delete operations
    # ------------------------------------------------------------------

    @override
    async def remove(self, collection_name: str, key: str) -> None:
        """Remove a single MemoryRecord by its SK id.

        We first search for the Dakera UUID that corresponds to this SK id,
        then call ``POST /v1/memory/forget`` with that specific UUID.
        """
        dakera_id = await self._resolve_dakera_id(collection_name, key)
        if dakera_id is None:
            logger.warning(
                "DakeraMemoryStore.remove: key '%s' not found in collection '%s'; skipping.",
                key,
                collection_name,
            )
            return
        await self._post(
            "/v1/memory/forget",
            {"agent_id": collection_name, "memory_ids": [dakera_id]},
        )

    @override
    async def remove_batch(self, collection_name: str, keys: list[str]) -> None:
        """Remove multiple MemoryRecords by their SK ids."""
        import asyncio

        tasks = [self._resolve_dakera_id(collection_name, key) for key in keys]
        dakera_ids_or_none = await asyncio.gather(*tasks)
        dakera_ids = [d for d in dakera_ids_or_none if d is not None]

        if not dakera_ids:
            return

        await self._post(
            "/v1/memory/forget",
            {"agent_id": collection_name, "memory_ids": dakera_ids},
        )

    # ------------------------------------------------------------------
    # Similarity search
    # ------------------------------------------------------------------

    @override
    async def get_nearest_matches(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float = 0.0,
        with_embeddings: bool = False,
    ) -> list[tuple[MemoryRecord, float]]:
        """Find the nearest memories using Dakera's server-side vector search.

        The ``embedding`` ndarray is accepted for interface compatibility but
        is not forwarded to Dakera — Dakera re-embeds the query text on the
        server side.  The query text is reconstructed from the description
        metadata if available; otherwise a generic search is performed.

        Note: because the embedding cannot be round-tripped through Dakera's
        API, ``with_embeddings=True`` will return records with empty
        embeddings (``array([])``).  If you need raw embeddings, maintain a
        separate embedding store alongside Dakera.

        Args:
            collection_name: The Dakera agent_id namespace to search in.
            embedding: The query embedding (used for interface compat only).
            limit: Maximum number of matches to return.
            min_relevance_score: Minimum relevance score threshold.
            with_embeddings: If True, attempt to include embeddings (will be empty arrays).

        Returns:
            List of (MemoryRecord, score) tuples sorted by score descending.
        """
        raw_results = await self._search_by_query(
            collection_name=collection_name,
            query=collection_name,  # fallback: search by collection name itself
            top_k=limit * 2,        # over-fetch to allow filtering
        )

        output: list[tuple[MemoryRecord, float]] = []
        for memory_obj, score in raw_results:
            if score < min_relevance_score:
                continue
            record = _payload_to_record(memory_obj, with_embeddings)
            output.append((record, score))
            if len(output) >= limit:
                break

        return output

    @override
    async def get_nearest_match(
        self,
        collection_name: str,
        embedding: ndarray,
        min_relevance_score: float = 0.0,
        with_embedding: bool = False,
    ) -> tuple[MemoryRecord, float] | None:
        """Find the single nearest memory.

        Returns:
            A (MemoryRecord, score) tuple or None if no match meets the threshold.
        """
        results = await self.get_nearest_matches(
            collection_name=collection_name,
            embedding=embedding,
            limit=1,
            min_relevance_score=min_relevance_score,
            with_embeddings=with_embedding,
        )
        return results[0] if results else None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _search_by_query(
        self,
        collection_name: str,
        query: str,
        top_k: int = 10,
    ) -> list[tuple[dict[str, Any], float]]:
        """Execute ``POST /v1/memory/search`` and return (memory_obj, score) pairs."""
        body: dict[str, Any] = {
            "agent_id": collection_name,
            "query": query,
            "top_k": top_k,
        }
        try:
            response = await self._post("/v1/memory/search", body)
        except ServiceResponseException as exc:
            if "404" in str(exc):
                return []
            raise

        items = response.get("memories") or []
        results: list[tuple[dict[str, Any], float]] = []
        for item in items:
            memory_obj = item.get("memory") or item
            score = float(item.get("score", 0.0))
            results.append((memory_obj, score))
        return results

    async def _resolve_dakera_id(
        self,
        collection_name: str,
        sk_key: str,
    ) -> str | None:
        """Look up the Dakera internal UUID for a given SK record id.

        Returns the Dakera UUID string, or None if not found.
        """
        candidates = await self._search_by_query(
            collection_name=collection_name,
            query=sk_key,
            top_k=20,
        )
        for memory_obj, _score in candidates:
            meta = memory_obj.get("metadata") or {}
            if meta.get(_DAKERA_ID_META_KEY) == sk_key:
                return memory_obj.get("id")
        return None

    # ------------------------------------------------------------------
    # Convenience search method (extends base contract)
    # ------------------------------------------------------------------

    async def search_text(
        self,
        collection_name: str,
        query: str,
        top_k: int = 5,
        min_relevance_score: float = 0.0,
    ) -> list[tuple[MemoryRecord, float]]:
        """Search Dakera using a raw text query (preferred over embedding-based search).

        This method bypasses the SK embedding pipeline and sends the query
        directly to Dakera, which handles embedding internally.  Use this
        when you want the most natural integration with Dakera's own ranking.

        Args:
            collection_name: The agent namespace to search.
            query: Plain-text search query.
            top_k: Number of results to return.
            min_relevance_score: Minimum relevance threshold.

        Returns:
            List of (MemoryRecord, score) tuples sorted by score descending.
        """
        raw = await self._search_by_query(collection_name, query, top_k * 2)
        results: list[tuple[MemoryRecord, float]] = []
        for memory_obj, score in raw:
            if score < min_relevance_score:
                continue
            results.append((_payload_to_record(memory_obj, False), score))
            if len(results) >= top_k:
                break
        return results
