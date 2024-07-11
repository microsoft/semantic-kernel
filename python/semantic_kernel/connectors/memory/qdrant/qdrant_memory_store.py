# Copyright (c) Microsoft. All rights reserved.

"""
QdrantMemoryStore provides functionality to add Qdrant vector database to support Semantic Kernel memory.
The QdrantMemoryStore inherits from MemoryStoreBase for persisting/retrieving data from a Qdrant Vector Database.
"""
import asyncio
import uuid
from logging import Logger
from typing import List, Optional, Tuple

from numpy import ndarray
from qdrant_client import QdrantClient
from qdrant_client import models as qdrant_models

from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.null_logger import NullLogger


class QdrantMemoryStore(MemoryStoreBase):
    _qdrantclient: QdrantClient
    _logger: Logger

    def __init__(
        self,
        vector_size: int,
        url: Optional[str] = None,
        port: Optional[int] = 6333,
        logger: Optional[Logger] = None,
        local: Optional[bool] = False,
    ) -> None:
        """Initializes a new instance of the QdrantMemoryStore class.

        Arguments:
            logger {Optional[Logger]} -- The logger to use. (default: {None})
        """
        if local:
            if url:
                self._qdrantclient = QdrantClient(location=url)
            else:
                self._qdrantclient = QdrantClient(location=":memory:")
        else:
            self._qdrantclient = QdrantClient(url=url, port=port)

        self._logger = logger or NullLogger()
        self._default_vector_size = vector_size

    async def create_collection_async(self, collection_name: str) -> None:
        """Creates a new collection if it does not exist.

        Arguments:
            collection_name {str} -- The name of the collection to create.
            vector_size {int} -- The size of the vector.
            distance {Optional[str]} -- The distance metric to use. (default: {"Cosine"})
        Returns:
            None
        """
        self._qdrantclient.recreate_collection(
            collection_name=collection_name,
            vectors_config=qdrant_models.VectorParams(
                size=self._default_vector_size, distance=qdrant_models.Distance.COSINE
            ),
        )

    async def get_collections_async(
        self,
    ) -> List[str]:
        """Gets the list of collections.

        Returns:
            List[str] -- The list of collections.
        """
        collection_info = self._qdrantclient.get_collections()
        return [collection.name for collection in collection_info.collections]

    async def get_collection_async(
        self, collection_name: str
    ) -> qdrant_models.CollectionInfo:
        """Gets the a collections based upon collection name.

        Returns:
            CollectionInfo -- Collection Information from Qdrant about collection.
        """
        collection_info = self._qdrantclient.get_collection(
            collection_name=collection_name
        )
        return collection_info

    async def delete_collection_async(self, collection_name: str) -> None:
        """Deletes a collection.

        Arguments:
            collection_name {str} -- The name of the collection to delete.

        Returns:
            None
        """

        self._qdrantclient.delete_collection(collection_name=collection_name)

    async def does_collection_exist_async(self, collection_name: str) -> bool:
        """Checks if a collection exists.

        Arguments:
            collection_name {str} -- The name of the collection to check.

        Returns:
            bool -- True if the collection exists; otherwise, False.
        """
        try:
            result = await self.get_collection_async(collection_name=collection_name)
            return result.status == qdrant_models.CollectionStatus.GREEN
        except ValueError:
            return False

    async def upsert_async(self, collection_name: str, record: MemoryRecord) -> str:
        """Upserts a record.

        Arguments:
            collection_name {str} -- The name of the collection to upsert the record into.
            record {MemoryRecord} -- The record to upsert.

        Returns:
            str -- The unique database key of the record.
        """
        data_to_upsert = await self._convert_from_memory_record_async(
            collection_name=collection_name,
            record=record,
        )

        result = self._qdrantclient.upsert(
            collection_name=collection_name,
            points=[data_to_upsert],
        )

        if result.status == qdrant_models.UpdateStatus.COMPLETED:
            return data_to_upsert.id
        else:
            raise Exception("Upsert failed")

    async def upsert_batch_async(
        self, collection_name: str, records: List[MemoryRecord]
    ) -> List[str]:
        tasks = []
        for record in records:
            tasks.append(
                self._convert_from_memory_record_async(
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
        else:
            raise Exception("Batch upsert failed")

    async def get_async(
        self, collection_name: str, key: str, with_embedding: bool = False
    ) -> Optional[MemoryRecord]:
        result = await self._get_existing_record_by_payload_id_async(
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
        else:
            return None

    async def get_batch_async(
        self, collection_name: str, keys: List[str], with_embeddings: bool = False
    ) -> List[MemoryRecord]:
        tasks = []
        for key in keys:
            tasks.append(
                self.get_async(
                    collection_name=collection_name,
                    key=key,
                    with_embedding=with_embeddings,
                )
            )
        return await asyncio.gather(*tasks)

    async def remove_async(self, collection_name: str, key: str) -> None:
        existing_record = await self._get_existing_record_by_payload_id_async(
            collection_name=collection_name,
            payload_id=key,
            with_embedding=False,
        )

        if existing_record:
            pointId = existing_record.id
            result = self._qdrantclient.delete(
                collection_name=collection_name, points_selector=[pointId]
            )
            if result.status != qdrant_models.UpdateStatus.COMPLETED:
                raise Exception("Delete failed")

    async def remove_batch_async(self, collection_name: str, keys: List[str]) -> None:
        tasks = []
        for key in keys:
            tasks.append(
                self._get_existing_record_by_payload_id_async(
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
                raise Exception("Delete failed")

    async def get_nearest_matches_async(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float,
        with_embeddings: bool = False,
    ) -> List[Tuple[MemoryRecord, float]]:
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

    async def get_nearest_match_async(
        self,
        collection_name: str,
        embedding: ndarray,
        min_relevance_score: float,
        with_embedding: bool = False,
    ) -> Tuple[MemoryRecord, float]:
        result = await self.get_nearest_matches_async(
            collection_name=collection_name,
            embedding=embedding,
            limit=1,
            min_relevance_score=min_relevance_score,
            with_embeddings=with_embedding,
        )
        return result[0] if result else None

    async def _get_existing_record_by_payload_id_async(
        self,
        collection_name: str,
        payload_id: str,
        with_embedding: bool = False,
    ) -> Optional[qdrant_models.ScoredPoint]:
        """Gets an existing record based upon payload id.

        Arguments:
            collection_name {str} -- The name of the collection.
            payload_id {str} -- The payload id to search for.

        Returns:
            Optional[ScoredPoint] -- The existing record if found; otherwise, None.
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
        else:
            return None

    async def _convert_from_memory_record_async(
        self, collection_name: str, record: MemoryRecord
    ) -> qdrant_models.PointStruct:
        if record._key is not None and record._key != "":
            pointId = record._key

        else:
            existing_record = await self._get_existing_record_by_payload_id_async(
                collection_name=collection_name,
                payload_id=record._id,
            )

            if existing_record:
                pointId = str(existing_record[0].id)
            else:
                pointId = str(uuid.uuid4())

        payload = record.__dict__.copy()
        embedding = payload.pop("_embedding")

        return qdrant_models.PointStruct(
            id=pointId, vector=embedding.tolist(), payload=payload
        )
