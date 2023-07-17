# Copyright (c) Microsoft. All rights reserved.

"""
QdrantMemoryStore provides functionality to add Qdrant vector database to support Semantic Kernel memory.
The QdrantMemoryStore inherits from MemoryStoreBase for persisting/retrieving data from a Qdrant Vector Database.
"""
import json
from logging import Logger
from typing import List, Optional, Tuple

from numpy import ndarray
from semantic_kernel.connectors.memory.qdrant.qdrant_utils import (
    convert_from_memory_record,
)

from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.null_logger import NullLogger

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, CollectionInfo
from qdrant_client.http.models import CollectionStatus, UpdateStatus, PointStruct


class QdrantMemoryStore(MemoryStoreBase):
    _qdrantclient: QdrantClient
    _logger: Logger

    def __init__(
        self,
        url: Optional[str] = None,
        port: Optional[int] = 6333,
        logger: Optional[Logger] = None,
        local: Optional[bool] = False,
    ) -> None:
        """Initializes a new instance of the QdrantMemoryStore class.

        Arguments:
            logger {Optional[Logger]} -- The logger to use. (default: {None})
        """
        try:
            from qdrant_client import QdrantClient
        except ImportError:
            raise ValueError(
                "Error: Unable to import qdrant client python package."
                "Please install qdrant client using `pip install qdrant-client`."
            )

        if local:
            if url:
                self._qdrantclient = QdrantClient(location=url)
            else:
                self._qdrantclient = QdrantClient(location=":memory:")
        else:
            self._qdrantclient = QdrantClient(url=url, port=port)

        self._logger = logger or NullLogger()

    async def create_collection_async(
        self, collection_name: str, vector_size: int
    ) -> None:
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
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
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

    async def get_collection_async(self, collection_name: str) -> CollectionInfo:
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
            return result.status == CollectionStatus.GREEN
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
        conv_result = convert_from_memory_record(
            self._qdrantclient, collection_name, record
        )

        collection_info = self.does_collection_exist_async(
            collection_name=collection_name
        )

        if not collection_info:
            raise Exception(f"Collection '{collection_name}' does not exist")

        payload_map = dict(
            id=record._id,
            description=record._description,
            text=record._text,
            additional_metadata=record._additional_metadata,
            external_source_name=record._external_source_name,
            timestamp=record._timestamp,
        )

        upsert_info = self._qdrantclient.upsert(
            collection_name=collection_name,
            wait=True,
            points=[
                PointStruct(
                    id=conv_result["pointid"],
                    vector=record._embedding,
                    payload=json.dumps(payload_map, default=str),
                ),
            ],
        )

        if upsert_info.status == UpdateStatus.COMPLETED:
            return record._key
        else:
            return ""

    async def upsert_batch_async(
        self, collection_name: str, records: List[MemoryRecord]
    ) -> List[str]:
        """Upserts a batch of records.

        Arguments:
            collection_name {str} -- The name of the collection to upsert the records into.
            records {List[MemoryRecord]} -- The records to upsert.

        Returns:
            List[str] -- The unique database keys of the records.
        """

        collection_info = self.does_collection_exist_async(
            collection_name=collection_name
        )

        if not collection_info:
            raise Exception(f"Collection '{collection_name}' does not exist")

        points_rec = []

        for record in records:
            conv_result = convert_from_memory_record(
                self._qdrantclient, collection_name, record
            )
            record._id = conv_result["pointid"]
            
            payload_map = dict(
                id=record._id,
                description=record._description,
                text=record._text,
                additional_metadata=record._additional_metadata,
                external_source_name=record._external_source_name,
                timestamp=record._timestamp,
            )

            pointstruct = PointStruct(
                id=conv_result["pointid"],
                vector=record._embedding,
                payload=json.dumps(payload_map, default=str),
            )
            points_rec.append([pointstruct])
            upsert_info = self._qdrantclient.upsert(
                collection_name=collection_name, wait=True, points=points_rec
            )

        if upsert_info.status == UpdateStatus.COMPLETED:
            return [record._id for record in records]
        else:
            return ""

    async def get_async(
        self, collection_name: str, key: str, with_embedding: bool = False
    ) -> MemoryRecord:
        """Gets a record.

        Arguments:
            collection_name {str} -- The name of the collection to get the record from.
            key {str} -- The unique database key of the record.
            with_embedding {bool} -- Whether to include the embedding in the result. (default: {False})

        Returns:
            MemoryRecord -- The record.
        """

        collection_info = self._qdrantclient.get_collection(
            collection_name=collection_name
        )
        with_payload = True
        search_id = [key]

        if not collection_info.status == CollectionStatus.GREEN:
            raise Exception(f"Collection '{collection_name}' does not exist")

        qdrant_record = self._qdrantclient.retrieve(
            collection_name=collection_name,
            ids=search_id,
            with_payload=with_payload,
            with_vectors=with_embedding,
        )

        result = MemoryRecord(
            is_reference=False,
            external_source_name="qdrant",
            key=search_id,
            id=search_id,
            embedding=qdrant_record.vector,
            payload=qdrant_record.payload,
        )

        return result

    async def get_batch_async(
        self, collection_name: str, keys: List[str], with_embeddings: bool = False
    ) -> List[MemoryRecord]:
        """Gets a batch of records.

        Arguments:
            collection_name {str} -- The name of the collection to get the records from.
            keys {List[str]} -- The unique database keys of the records.
            with_embeddings {bool} -- Whether to include the embeddings in the results. (default: {False})

        Returns:
            List[MemoryRecord] -- The records.
        """

        collection_info = self._qdrantclient.get_collection(
            collection_name=collection_name
        )

        if not collection_info.status == CollectionStatus.GREEN:
            raise Exception(f"Collection '{collection_name}' does not exist")

        with_payload = True
        search_ids = [keys]

        qdrant_records = self._qdrantclient.retrieve(
            collection_name=collection_name,
            ids=search_ids,
            with_payload=with_payload,
            with_vectors=with_embeddings,
        )

        return qdrant_records

    async def remove_async(self, collection_name: str, key: str) -> None:
        """Removes a record.

        Arguments:
            collection_name {str} -- The name of the collection to remove the record from.
            key {str} -- The unique database key of the record to remove.

        Returns:
            None
        """

        collection_info = self._qdrantclient.get_collection(
            collection_name=collection_name
        )

        if not collection_info.status == CollectionStatus.GREEN:
            raise Exception(f"Collection '{collection_name}' does not exist")

        self._qdrantclient.delete(
            collection_name=collection_name,
            points_selector=models.PointIdsList(
                points=[key],
            ),
        )

    async def remove_batch_async(self, collection_name: str, keys: List[str]) -> None:
        """Removes a batch of records.

        Arguments:
            collection_name {str} -- The name of the collection to remove the records from.
            keys {List[str]} -- The unique database keys of the records to remove.

        Returns:
            None
        """
        collection_info = self._qdrantclient.get_collection(
            collection_name=collection_name
        )

        if not collection_info.status == CollectionStatus.GREEN:
            raise Exception(f"Collection '{collection_name}' does not exist")

        self._qdrantclient.delete(
            collection_name=collection_name,
            points_selector=models.PointIdsList(
                points=[keys],
            ),
        )

    async def get_nearest_match_async(
        self,
        collection_name: str,
        embedding: ndarray,
        min_relevance_score: float = 0.0,
        with_embedding: bool = False,
    ) -> Tuple[MemoryRecord, float]:
        """Gets the nearest match to an embedding using cosine similarity.

        Arguments:
            collection_name {str} -- The name of the collection to get the nearest match from.
            embedding {ndarray} -- The embedding to find the nearest match to.
            min_relevance_score {float} -- The minimum relevance score of the match. (default: {0.0})
            with_embedding {bool} -- Whether to include the embedding in the result. (default: {False})

        Returns:
            Tuple[MemoryRecord, float] -- The record and the relevance score.
        """
        return self.get_nearest_matches_async(
            collection_name=collection_name,
            embedding=embedding,
            limit=1,
            min_relevance_score=min_relevance_score,
            with_embeddings=with_embedding,
        )

    async def get_nearest_matches_async(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float = 0.0,
        with_embeddings: bool = False,
    ) -> List[Tuple[MemoryRecord, float]]:
        """Gets the nearest matches to an embedding using cosine similarity.

        Arguments:
            collection_name {str} -- The name of the collection to get the nearest matches from.
            embedding {ndarray} -- The embedding to find the nearest matches to.
            limit {int} -- The maximum number of matches to return.
            min_relevance_score {float} -- The minimum relevance score of the matches. (default: {0.0})
            with_embeddings {bool} -- Whether to include the embeddings in the results. (default: {False})

        Returns:
            List[Tuple[MemoryRecord, float]] -- The records and their relevance scores.
        """

        collection_info = self._qdrantclient.get_collection(
            collection_name=collection_name
        )

        if not collection_info.status == CollectionStatus.GREEN:
            raise Exception(f"Collection '{collection_name}' does not exist")

        # Search for the nearest matches, qdrant already provides results sorted by relevance score
        qdrant_matches = self._qdrantclient.search(
            collection_name=collection_name,
            search_params=models.SearchParams(
                hnsw_ef=0,
                exact=False,
                quantization=None,
            ),
            query_vector=embedding,
            limit=limit,
            score_threshold=min_relevance_score,
            with_vectors=with_embeddings,
            with_payload=True,
        )

        nearest_results = []

        # Convert the results to MemoryRecords
        for qdrant_match in qdrant_matches:
            vector_result = MemoryRecord(
                is_reference=False,
                external_source_name="qdrant",
                key=None,
                id=str(qdrant_match.id),
                embedding=qdrant_match.vector,
                payload=qdrant_match.payload,
            )

            nearest_results.append(tuple(vector_result, qdrant_match.score))

        return nearest_results
