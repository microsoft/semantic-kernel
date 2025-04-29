# Copyright (c) Microsoft. All rights reserved.

import json
import sys
from typing import Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

import numpy as np
from azure.cosmos.aio import ContainerProxy, CosmosClient, DatabaseProxy
from numpy import ndarray

from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class AzureCosmosDBNoSQLMemoryStore(MemoryStoreBase):
    """You can read more about vector search using AzureCosmosDBNoSQL here: https://aka.ms/CosmosVectorSearch."""

    cosmos_client: CosmosClient = None
    database: DatabaseProxy
    container: ContainerProxy
    database_name: str = None
    partition_key: str = None
    vector_embedding_policy: dict[str, Any] | None = None
    indexing_policy: dict[str, Any] | None = None
    cosmos_container_properties: dict[str, Any] | None = None

    def __init__(
        self,
        cosmos_client: CosmosClient,
        database_name: str,
        partition_key: str,
        vector_embedding_policy: dict[str, Any] | None = None,
        indexing_policy: dict[str, Any] | None = None,
        cosmos_container_properties: dict[str, Any] | None = None,
    ):
        """Initializes a new instance of the AzureCosmosDBNoSQLMemoryStore class."""
        if indexing_policy["vectorIndexes"] is None or len(indexing_policy["vectorIndexes"]) == 0:
            raise ValueError("vectorIndexes cannot be null or empty in the indexing_policy.")
        if vector_embedding_policy is None or len(vector_embedding_policy["vectorEmbeddings"]) == 0:
            raise ValueError("vectorEmbeddings cannot be null or empty in the vector_embedding_policy.")

        self.cosmos_client = cosmos_client
        self.database_name = database_name
        self.partition_key = partition_key
        self.vector_embedding_policy = vector_embedding_policy
        self.indexing_policy = indexing_policy
        self.cosmos_container_properties = cosmos_container_properties

    @override
    async def create_collection(self, collection_name: str) -> None:
        # Create the database if it already doesn't exist
        self.database = await self.cosmos_client.create_database_if_not_exists(id=self.database_name)

        # Create the collection if it already doesn't exist
        self.container = await self.database.create_container_if_not_exists(
            id=collection_name,
            partition_key=self.cosmos_container_properties["partition_key"],
            indexing_policy=self.indexing_policy,
            vector_embedding_policy=self.vector_embedding_policy,
        )

    @override
    async def get_collections(self) -> list[str]:
        return [container["id"] async for container in self.database.list_containers()]

    @override
    async def delete_collection(self, collection_name: str) -> None:
        return await self.database.delete_container(collection_name)

    @override
    async def does_collection_exist(self, collection_name: str) -> bool:
        return collection_name in [container["id"] async for container in self.database.list_containers()]

    @override
    async def upsert(self, collection_name: str, record: MemoryRecord) -> str:
        result = await self.upsert_batch(collection_name, [record])
        return result[0]

    @override
    async def upsert_batch(self, collection_name: str, records: list[MemoryRecord]) -> list[str]:
        doc_ids: list[str] = []
        for record in records:
            cosmosRecord: dict = {
                "id": record.id,
                "embedding": record.embedding.tolist(),
                "text": record.text,
                "description": record.description,
                "metadata": self.__serialize_metadata(record),
            }
            if record.timestamp is not None:
                cosmosRecord["timeStamp"] = record.timestamp

            await self.container.create_item(cosmosRecord)
            doc_ids.append(cosmosRecord["id"])
        return doc_ids

    @override
    async def get(self, collection_name: str, key: str, with_embedding: bool) -> MemoryRecord:
        item = await self.container.read_item(key, partition_key=key)
        return MemoryRecord.local_record(
            id=item["id"],
            embedding=np.array(item["embedding"]) if with_embedding else np.array([]),
            text=item["text"],
            description=item["description"],
            additional_metadata=item["metadata"],
            timestamp=item.get("timestamp", None),
        )

    @override
    async def get_batch(self, collection_name: str, keys: list[str], with_embeddings: bool) -> list[MemoryRecord]:
        query = "SELECT * FROM c WHERE ARRAY_CONTAINS(@ids, c.id)"
        parameters = [{"name": "@ids", "value": keys}]

        all_results = []
        items = [item async for item in self.container.query_items(query, parameters=parameters)]
        for item in items:
            MemoryRecord.local_record(
                id=item["id"],
                embedding=np.array(item["embedding"]) if with_embeddings else np.array([]),
                text=item["text"],
                description=item["description"],
                additional_metadata=item["metadata"],
                timestamp=item.get("timestamp", None),
            )
            all_results.append(item)
        return all_results

    @override
    async def remove(self, collection_name: str, key: str) -> None:
        await self.container.delete_item(key, partition_key=key)

    @override
    async def remove_batch(self, collection_name: str, keys: list[str]) -> None:
        for key in keys:
            await self.container.delete_item(key, partition_key=key)

    @override
    async def get_nearest_matches(
        self, collection_name: str, embedding: ndarray, limit: int, min_relevance_score: float, with_embeddings: bool
    ) -> list[tuple[MemoryRecord, float]]:
        embedding_key = self.vector_embedding_policy["vectorEmbeddings"][0]["path"][1:]
        query = (
            f"SELECT TOP {limit} c.id, c.{embedding_key}, c.text, c.description, c.metadata, "  # nosec
            f"c.timestamp, VectorDistance(c.{embedding_key}, {embedding.tolist()}) AS SimilarityScore FROM c ORDER BY "  # nosec
            f"VectorDistance(c.{embedding_key}, {embedding.tolist()})"  # nosec
        )

        items = [item async for item in self.container.query_items(query=query)]
        nearest_results = []
        for item in items:
            score = item["SimilarityScore"]
            if score < min_relevance_score:
                continue
            result = MemoryRecord.local_record(
                id=item["id"],
                embedding=np.array(item["embedding"]) if with_embeddings else np.array([]),
                text=item["text"],
                description=item["description"],
                additional_metadata=item["metadata"],
                timestamp=item.get("timestamp", None),
            )
            nearest_results.append((result, score))
        return nearest_results

    @override
    async def get_nearest_match(
        self, collection_name: str, embedding: ndarray, min_relevance_score: float, with_embedding: bool
    ) -> tuple[MemoryRecord, float]:
        nearest_results = await self.get_nearest_matches(
            collection_name=collection_name,
            embedding=embedding,
            limit=1,
            min_relevance_score=min_relevance_score,
            with_embeddings=with_embedding,
        )
        if len(nearest_results) > 0:
            return nearest_results[0]
        return None

    @staticmethod
    def __serialize_metadata(record: MemoryRecord) -> str:
        return json.dumps({
            "text": record.text,
            "description": record.description,
            "additional_metadata": record.additional_metadata,
        })
