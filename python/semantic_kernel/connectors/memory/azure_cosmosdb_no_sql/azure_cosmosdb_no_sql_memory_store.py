# Copyright (c) Microsoft. All rights reserved.

import json
from typing import Any, Dict, List, Tuple

import numpy as np
from azure.cosmos.aio import ContainerProxy, CosmosClient, DatabaseProxy
from numpy import ndarray
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase

from python.semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


class AzureCosmosDBNoSQLMemoryStore(MemoryStoreBase):
    cosmos_client: CosmosClient = None
    database: DatabaseProxy
    container: ContainerProxy
    database_name: str = None
    partition_key: str = None
    vector_embedding_policy: [Dict[str, Any]] = None
    indexing_policy: [Dict[str, Any]] = None
    cosmos_container_properties: [Dict[str, Any]] = None

    def __init__(
        self,
        cosmos_client: CosmosClient,
        database_name: str,
        partition_key: str,
        vector_embedding_policy: [Dict[str, Any]],
        indexing_policy: [Dict[str, Any]],
        cosmos_container_properties: [Dict[str, Any]],
    ):
        if indexing_policy["vectorIndexes"] is None or len(indexing_policy["vectorIndexes"]):
            raise ServiceInitializationError("Vector dimensions must be a positive number.")

        self.cosmos_client = cosmos_client
        self.database_name = database_name
        self.partition_key = partition_key
        self.vector_embedding_policy = vector_embedding_policy
        self.indexing_policy = indexing_policy
        self.cosmos_container_properties = cosmos_container_properties

    async def create_collection_async(self, collection_name: str) -> None:
        # Create the database if it already doesn't exist
        self.database = await self.cosmos_client.create_database_if_not_exists(id=self.database_name)

        # Create the collection if it already doesn't exist
        self.container = await self.database.create_container_if_not_exists(
            id=collection_name,
            partition_key=self.cosmos_container_properties["partition_key"],
            indexing_policy=self.indexing_policy,
            vector_embedding_policy=self.vector_embedding_policy,
            default_ttl=self.cosmos_container_properties["default_ttl"],
            populate_query_metrics=self.cosmos_container_properties["populate_query_metrics"],
            offer_throughput=self.cosmos_container_properties["offer_throughput"],
            unique_key_policy=self.cosmos_container_properties["unique_key_policy"],
            conflict_resolution_policy=self.cosmos_container_properties["conflict_resolution_policy"],
            session_token=self.cosmos_container_properties["session_token"],
            initial_headers=self.cosmos_container_properties["initial_headers"],
            etag=self.cosmos_container_properties["etag"],
            match_condition=self.cosmos_container_properties["match_condition"],
            analytical_storage_ttl=self.cosmos_container_properties["analytical_storage_ttl"],
        )

    async def get_collections_async(self) -> List[str]:
        return list(self.database.list_containers())

    async def delete_collection_async(self, collection_name: str) -> None:
        return await self.database.delete_container(collection_name)

    async def does_collection_exist_async(self, collection_name: str) -> bool:
        return collection_name in list(self.database.list_containers())

    async def upsert_async(self, collection_name: str, record: MemoryRecord) -> str:
        result = await self.upsert_batch_async(collection_name, [record])
        return result[0]

    async def upsert_batch_async(self, collection_name: str, records: List[MemoryRecord]) -> List[str]:
        doc_ids: List[str] = []
        for record in records:
            cosmosRecord: dict = {
                "_id": record.id,
                "embedding": record.embedding.tolist(),
                "text": record.text,
                "description": record.description,
                "metadata": self.__serialize_metadata(record),
            }
            if record.timestamp is not None:
                cosmosRecord["timeStamp"] = record.timestamp

            self.container.create_item(cosmosRecord)
            doc_ids.append(cosmosRecord["_id"])
        return doc_ids

    async def get_async(self, collection_name: str, key: str, with_embedding: bool) -> MemoryRecord:
        item = await self.container.read_item(key, self.partition_key)
        return MemoryRecord.local_record(
            id=item["_id"],
            embedding=np.array(item["embedding"]) if with_embedding else np.array([]),
            text=item["text"],
            description=item["description"],
            additional_metadata=item["metadata"],
            timestamp=item.get("timestamp", None),
        )

    async def get_batch_async(self, collection_name: str, keys: List[str], with_embeddings: bool) -> List[MemoryRecord]:
        query = "SELECT * FROM c WHERE c._id IN @ids"
        parameters = [{"name": "@ids", "value": keys}]

        query_iterable = self.container.query_items(query)
        all_results = []
        pages = query_iterable.by_page()
        async for items in await pages.__anext__():
            for item in items:
                MemoryRecord.local_record(
                    id=item["_id"],
                    embedding=np.array(item["embedding"]) if with_embeddings else np.array([]),
                    text=item["text"],
                    description=item["description"],
                    additional_metadata=item["metadata"],
                    timestamp=item.get("timestamp", None),
                )
                all_results.append(item)
        return all_results

    async def remove_async(self, collection_name: str, key: str) -> None:
        self.container.delete_item(key)

    async def remove_batch_async(self, collection_name: str, keys: List[str]) -> None:
        for key in keys:
            self.container.delete_item(key)

    async def get_nearest_matches_async(self, collection_name: str, embedding: ndarray, limit: int,
                                        min_relevance_score: float, with_embeddings: bool) -> List[
        Tuple[MemoryRecord, float]]:
        embedding_key = self.vector_embedding_policy["vectorEmbeddings"][0]["path"]
        query = ("SELECT TOP {} c._id, c.{}, c.text, c.description, c.additional_metadata, "
                 "c.timestamp, VectorDistance(c.{}, {}) AS SimilarityScore FROM c ORDER BY "
                 "VectorDistance(c.{}, {})".format(limit, embedding_key, embedding_key, embedding, embedding_key,
                                                   embedding))

        items = [item async for item in self.container.query_items(query=query)]
        nearest_results = []
        for item in items:
            score = item["SimilarityScore"]
            if score < min_relevance_score:
                continue
            result = MemoryRecord.local_record(
                id=item["_id"],
                embedding=np.array(item["embedding"]) if with_embeddings else np.array([]),
                text=item["text"],
                description=item["description"],
                additional_metadata=item["metadata"],
                timestamp=item.get("timestamp", None),
            )
            nearest_results.append((result, score))
        return nearest_results

    async def get_nearest_match_async(self, collection_name: str, embedding: ndarray, min_relevance_score: float,
                                      with_embedding: bool) -> Tuple[MemoryRecord, float]:
        nearest_results = await self.get_nearest_matches_async(collection_name=collection_name,
                                                               embedding=embedding,
                                                               limit=1,
                                                               min_relevance_score=min_relevance_score,
                                                               with_embeddings=with_embedding, )
        if len(nearest_results) > 0:
            return nearest_results[0]
        else:
            return None

    @staticmethod
    def __serialize_metadata(record: MemoryRecord) -> str:
        return json.dumps(
            {
                "text": record.text,
                "description": record.description,
                "additional_metadata": record.additional_metadata,
            }
        )
