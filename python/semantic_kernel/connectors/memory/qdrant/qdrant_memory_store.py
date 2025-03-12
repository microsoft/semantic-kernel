# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import sys
import uuid

from numpy import ndarray
from qdrant_client import QdrantClient
from qdrant_client import models as qdrant_models

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

from semantic_kernel.exceptions import ServiceResponseException
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.feature_stage_decorator import experimental

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class QdrantMemoryStore(MemoryStoreBase):
    """QdrantMemoryStore."""

    _qdrantclient: QdrantClient

    def __init__(
        self,
        vector_size: int,
        url: str | None = None,
        port: int | None = 6333,
        local: bool | None = False,
        **kwargs,
    ) -> None:
        """Initializes a new instance of the QdrantMemoryStore class."""
        if local:
            if url:
                self._qdrantclient = QdrantClient(location=url)
            else:
                self._qdrantclient = QdrantClient(location=":memory:")
        else:
            self._qdrantclient = QdrantClient(url=url, port=port)

        self._default_vector_size = vector_size

    @override
    async def create_collection(self, collection_name: str) -> None:
        self._qdrantclient.recreate_collection(
            collection_name=collection_name,
            vectors_config=qdrant_models.VectorParams(
                size=self._default_vector_size, distance=qdrant_models.Distance.COSINE
            ),
        )

    @override
    async def get_collections(
        self,
    ) -> list[str]:
        collection_info = self._qdrantclient.get_collections()
        return [collection.name for collection in collection_info.collections]

    async def get_collection(self, collection_name: str) -> qdrant_models.CollectionInfo:
        """Gets the collection based upon collection name.

        Returns:
            CollectionInfo -- Collection Information from Qdrant about collection.
        """
        return self._qdrantclient.get_collection(collection_name=collection_name)

    @override
    async def delete_collection(self, collection_name: str) -> None:
        self._qdrantclient.delete_collection(collection_name=collection_name)

    @override
    async def does_collection_exist(self, collection_name: str) -> bool:
        return self._qdrantclient.collection_exists(collection_name=collection_name)

    @override
    async def upsert(self, collection_name: str, record: MemoryRecord) -> str:
        data_to_upsert = await self._convert_from_memory_record(
            collection_name=collection_name,
            record=record,
        )

        result = self._qdrantclient.upsert(
            collection_name=collection_name,
            points=[data_to_upsert],
        )

        if result.status == qdrant_models.UpdateStatus.COMPLETED:
            return data_to_upsert.id
        raise ServiceResponseException("Upsert failed")

    @override
    async def upsert_batch(self, collection_name: str, records: list[MemoryRecord]) -> list[str]:
        tasks = []
        for record in records:
            tasks.append(
                self._convert_from_memory_record(
                    collection_name=collection_name,
                    record=record,
                )
            )

        data_to_upsert = await asyncio.gather(*tasks)

        result = self._qdrantclient.upsert(
            collection_name=collection_name,
            points=data_to_upsert,
        )

        if result.status == qdrant_models.UpdateStatus.COMPLETED:
            return [data.id for data in data_to_upsert]
        raise ServiceResponseException("Batch upsert failed")

    @override
    async def get(self, collection_name: str, key: str, with_embedding: bool = False) -> MemoryRecord | None:
        result = await self._get_existing_record_by_payload_id(
            collection_name=collection_name,
            payload_id=key,
            with_embedding=with_embedding,
        )

        if result:
            return MemoryRecord(
                is_reference=result.payload["_is_reference"],
                external_source_name=result.payload["_external_source_name"],
                id=result.payload["_id"],
                description=result.payload["_description"],
                text=result.payload["_text"],
                additional_metadata=result.payload["_additional_metadata"],
                embedding=result.vector,
                key=result.id,
                timestamp=result.payload["_timestamp"],
            )
        return None

    @override
    async def get_batch(
        self,
        collection_name: str,
        keys: list[str],
        with_embeddings: bool = False,
    ) -> list[MemoryRecord]:
        tasks = []
        for key in keys:
            tasks.append(
                self.get(
                    collection_name=collection_name,
                    key=key,
                    with_embedding=with_embeddings,
                )
            )
        return await asyncio.gather(*tasks)

    @override
    async def remove(self, collection_name: str, key: str) -> None:
        existing_record = await self._get_existing_record_by_payload_id(
            collection_name=collection_name,
            payload_id=key,
            with_embedding=False,
        )

        if existing_record:
            pointId = existing_record.id
            result = self._qdrantclient.delete(collection_name=collection_name, points_selector=[pointId])
            if result.status != qdrant_models.UpdateStatus.COMPLETED:
                raise ServiceResponseException("Delete failed")

    @override
    async def remove_batch(self, collection_name: str, keys: list[str]) -> None:
        tasks = []
        for key in keys:
            tasks.append(
                self._get_existing_record_by_payload_id(
                    collection_name=collection_name,
                    payload_id=key,
                    with_embedding=False,
                )
            )

        existing_records = await asyncio.gather(*tasks)

        if len(existing_records) > 0:
            result = self._qdrantclient.delete(
                collection_name=collection_name,
                points_selector=[record.id for record in existing_records],
            )
            if result.status != qdrant_models.UpdateStatus.COMPLETED:
                raise ServiceResponseException("Delete failed")

    @override
    async def get_nearest_matches(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float,
        with_embeddings: bool = False,
    ) -> list[tuple[MemoryRecord, float]]:
        match_results = self._qdrantclient.search(
            collection_name=collection_name,
            query_vector=embedding,
            limit=limit,
            score_threshold=min_relevance_score,
            with_vectors=with_embeddings,
        )

        return [
            (
                MemoryRecord(
                    is_reference=result.payload["_is_reference"],
                    external_source_name=result.payload["_external_source_name"],
                    id=result.payload["_id"],
                    description=result.payload["_description"],
                    text=result.payload["_text"],
                    additional_metadata=result.payload["_additional_metadata"],
                    embedding=result.vector,
                    key=result.id,
                    timestamp=result.payload["_timestamp"],
                ),
                result.score,
            )
            for result in match_results
        ]

    @override
    async def get_nearest_match(
        self,
        collection_name: str,
        embedding: ndarray,
        min_relevance_score: float,
        with_embedding: bool = False,
    ) -> tuple[MemoryRecord, float]:
        result = await self.get_nearest_matches(
            collection_name=collection_name,
            embedding=embedding,
            limit=1,
            min_relevance_score=min_relevance_score,
            with_embeddings=with_embedding,
        )
        return result[0] if result else None

    async def _get_existing_record_by_payload_id(
        self,
        collection_name: str,
        payload_id: str,
        with_embedding: bool = False,
    ) -> qdrant_models.ScoredPoint | None:
        """Gets an existing record based upon payload id.

        Args:
            collection_name (str): The name of the collection.
            payload_id (str): The payload id to search for.
            with_embedding (bool): If true, the embedding will be returned in the memory records.

        Returns:
            Optional[ScoredPoint]: The existing record if found; otherwise, None.
        """
        filter = qdrant_models.Filter(
            must=[
                qdrant_models.FieldCondition(
                    key="_id",
                    match=qdrant_models.MatchText(text=payload_id),
                )
            ]
        )

        existing_record = self._qdrantclient.search(
            collection_name=collection_name,
            query_vector=[0.0] * self._default_vector_size,
            limit=1,
            query_filter=filter,
            with_payload=True,
            with_vectors=with_embedding,
        )

        if existing_record:
            return existing_record[0]
        return None

    async def _convert_from_memory_record(
        self, collection_name: str, record: MemoryRecord
    ) -> qdrant_models.PointStruct:
        if record._key is not None and record._key != "":
            pointId = record._key

        else:
            existing_record = await self._get_existing_record_by_payload_id(
                collection_name=collection_name,
                payload_id=record._id,
            )

            pointId = str(existing_record.id) if existing_record else str(uuid.uuid4())

        payload = record.__dict__.copy()
        embedding = payload.pop("_embedding")

        return qdrant_models.PointStruct(id=pointId, vector=embedding.tolist(), payload=payload)
