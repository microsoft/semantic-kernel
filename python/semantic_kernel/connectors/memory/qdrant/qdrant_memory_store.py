# Copyright (c) Microsoft. All rights reserved.

"""
QdrantMemoryStore provides functionality to add Qdrant vector database to support Semantic Kernel memory.
The QdrantMemoryStore inherits from MemoryStoreBase for persisting/retrieving data from a Qdrant Vector Database.
"""
import json
from logging import Logger
from typing import List, Optional, Tuple
import uuid

from numpy import ndarray
from semantic_kernel.connectors.memory.qdrant.qdrant_utils import (
    convert_from_memory_record,
)

from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.null_logger import NullLogger

from qdrant_client import QdrantClient
from qdrant_client import models as qdrant_models


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
            vectors_config=qdrant_models.VectorParams(size=vector_size, distance=qdrant_models.Distance.COSINE),
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

    async def get_collection_async(self, collection_name: str) -> qdrant_models.CollectionInfo:
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
        if record._key is not None and record._key != "":
            pointId = record._key
        else:
            payload_filter = qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="id",
                        match=qdrant_models.MatchValue(value=record._id),
                    )
                ]
            )
            # check for existing record based on payload content for id
            existing_record = self._qdrantclient.retrieve(
                collection_name=collection_name,
                ids=[record._id],
            )

            if existing_record:
                pointId = str(existing_record[0].id)
            else:
                pointId = str(uuid.uuid4())

    async def upsert_async(self, collection_name: str, record: MemoryRecord) -> str:
        pass

    async def upsert_batch_async(
        self, collection_name: str, records: List[MemoryRecord]
    ) -> List[str]:
        pass

    async def get_async(
        self, collection_name: str, key: str, with_embedding: bool
    ) -> MemoryRecord:
        pass

    async def get_batch_async(
        self, collection_name: str, keys: List[str], with_embeddings: bool
    ) -> List[MemoryRecord]:
        pass

    async def remove_async(self, collection_name: str, key: str) -> None:
        pass

    async def remove_batch_async(self, collection_name: str, keys: List[str]) -> None:
        pass

    async def get_nearest_matches_async(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float,
        with_embeddings: bool,
    ) -> List[Tuple[MemoryRecord, float]]:
        pass

    async def get_nearest_match_async(
        self,
        collection_name: str,
        embedding: ndarray,
        min_relevance_score: float,
        with_embedding: bool,
    ) -> Tuple[MemoryRecord, float]:
        pass

    async def convert_from_memory_record(
        self, collection_name: str, record: MemoryRecord
    ):
        """Converts a memory record to a Qdrant vector record.

        Arguments:
            collection_name {str} -- The name of the collection.
            record {MemoryRecord} -- The memory record.

        Returns:
        """
        if record._key is not None and record._key != "":
            point_id = record._key
        else:
            # check for existing record based on payload content for id
            existing_record = self._qdrantclient.retrieve(
                collection_name=collection_name,
                ids=[record._id],
            )


            point_id = uuid.uuid4()