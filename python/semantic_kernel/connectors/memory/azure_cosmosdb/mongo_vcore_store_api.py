# Copyright (c) Microsoft. All rights reserved.

import json
from typing import List, Tuple

import numpy as np

from semantic_kernel.connectors.memory.azure_cosmosdb.azure_cosmos_db_store_api import (
    AzureCosmosDBStoreApi,
)
from semantic_kernel.memory.memory_record import MemoryRecord


class MongoStoreApi(AzureCosmosDBStoreApi):
    database = None
    collection_name: str
    index_name = None
    vector_dimensions = None
    num_lists = None
    similarity = None
    collection = None

    def __init__(
        self,
        collection_name: str,
        index_name: str,
        vector_dimensions: int,
        num_lists: int,
        similarity: str,
        database=None,
    ):
        self.database = database
        self.collection_name = collection_name
        self.index_name = index_name
        self.num_lists = num_lists
        self.similarity = similarity
        self.vector_dimensions = vector_dimensions

    async def create_collection(self, collection_name: str) -> None:
        if not await self.does_collection_exist(collection_name):
            if self.index_name not in self.database[collection_name].list_indexes():
                self.database.command(
                    {
                        "createIndexes": collection_name,
                        "indexes": [
                            {
                                "name": self.index_name,
                                "key": {"embedding": "cosmosSearch"},
                                "cosmosSearchOptions": {
                                    "kind": "vector-ivf",
                                    "numLists": self.num_lists,
                                    "similarity": self.similarity,
                                    "dimensions": self.vector_dimensions,
                                },
                            }
                        ],
                    }
                )
        self.collection = self.database[collection_name]

    async def get_collections(self) -> List[str]:
        return self.database.list_collection_names()

    async def delete_collection(self, collection_name: str) -> None:
        return self.collection.drop()

    async def does_collection_exist(self, collection_name: str) -> bool:
        return collection_name in self.database.list_collection_names()

    async def upsert(self, collection_name: str, record: MemoryRecord) -> str:
        result = await self.upsert_batch(collection_name, [record])
        return result[0]

    async def upsert_batch(self, collection_name: str, records: List[MemoryRecord]) -> List[str]:
        doc_ids: List[str] = []
        cosmosRecords: List[dict] = []
        for record in records:
            cosmosRecord: dict = {
                "_id": record.id,
                "embedding": record.embedding.tolist(),
                "text": record.text,
                "description": record.description,
                "metadata": self.__serialize_metadata(record),
            }
            if record.timestamp is not None:
                cosmosRecord["timestamp"] = record.timestamp

            doc_ids.append(cosmosRecord["_id"])
            cosmosRecords.append(cosmosRecord)
        self.collection.insert_many(cosmosRecords)
        return doc_ids

    async def get(self, collection_name: str, key: str, with_embedding: bool) -> MemoryRecord:
        if not with_embedding:
            result = self.collection.find_one({"_id": key}, {"embedding": 0})
        else:
            result = self.collection.find_one({"_id": key})
        return MemoryRecord.local_record(
            id=result["_id"],
            embedding=np.array(result["embedding"]) if with_embedding else np.array([]),
            text=result["text"],
            description=result["description"],
            additional_metadata=result["metadata"],
            timestamp=result.get("timestamp", None),
        )

    async def get_batch(self, collection_name: str, keys: List[str], with_embeddings: bool) -> List[MemoryRecord]:
        if not with_embeddings:
            results = self.collection.find({"_id": {"$in": keys}}, {"embedding": 0})
        else:
            results = self.collection.find({"_id": {"$in": keys}})

        return [
            MemoryRecord.local_record(
                id=result["_id"],
                embedding=np.array(result["embedding"]) if with_embeddings else np.array([]),
                text=result["text"],
                description=result["description"],
                additional_metadata=result["metadata"],
                timestamp=result.get("timestamp", None),
            )
            for result in results
        ]

    async def remove(self, collection_name: str, key: str) -> None:
        self.collection.delete_one({"_id": key})

    async def remove_batch(self, collection_name: str, keys: List[str]) -> None:
        self.collection.delete_many({"_id": {"$in": keys}})

    async def get_nearest_matches(
        self,
        collection_name: str,
        embedding: np.ndarray,
        limit: int,
        min_relevance_score: float,
        with_embeddings: bool,
    ) -> List[Tuple[MemoryRecord, float]]:
        pipeline = [
            {
                "$search": {
                    "cosmosSearch": {
                        "vector": embedding.tolist(),
                        "path": "embedding",
                        "k": limit,
                    },
                    "returnStoredSource": True,
                }
            },
            {
                "$project": {
                    "similarityScore": {"$meta": "searchScore"},
                    "document": "$$ROOT",
                }
            },
        ]
        nearest_results = []
        # Perform vector search
        for aggResult in self.collection.aggregate(pipeline):
            result = MemoryRecord.local_record(
                id=aggResult["_id"],
                embedding=np.array(aggResult["document"]["embedding"]) if with_embeddings else np.array([]),
                text=aggResult["document"]["text"],
                description=aggResult["document"]["description"],
                additional_metadata=aggResult["document"]["metadata"],
                timestamp=aggResult["document"].get("timestamp", None),
            )
            if aggResult["similarityScore"] < min_relevance_score:
                continue
            else:
                nearest_results.append((result, aggResult["similarityScore"]))
        return nearest_results

    async def get_nearest_match(
        self,
        collection_name: str,
        embedding: np.ndarray,
        min_relevance_score: float,
        with_embedding: bool,
    ) -> Tuple[MemoryRecord, float]:
        nearest_results = await self.get_nearest_matches(
            collection_name=collection_name,
            embedding=embedding,
            min_relevance_score=min_relevance_score,
            with_embeddings=with_embedding,
            limit=1,
        )

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
