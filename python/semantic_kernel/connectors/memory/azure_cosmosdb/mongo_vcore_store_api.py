# Copyright (c) Microsoft. All rights reserved.

import json
import sys
from typing import Any

if sys.version >= "3.12":
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

import numpy as np

from semantic_kernel.connectors.memory.azure_cosmosdb.azure_cosmos_db_store_api import AzureCosmosDBStoreApi
from semantic_kernel.connectors.memory.azure_cosmosdb.utils import CosmosDBSimilarityType, CosmosDBVectorSearchType
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class MongoStoreApi(AzureCosmosDBStoreApi):
    """MongoStoreApi class for the Azure Cosmos DB Mongo store."""

    database = None
    collection_name: str
    index_name = None
    vector_dimensions = None
    num_lists = None
    similarity = None
    collection = None
    kind = None
    m = None
    ef_construction = None
    ef_search = None

    """
    Args:
        collection_name: Name of the collection for the azure cosmos db mongo store
        index_name: Index for the collection
        vector_dimensions: Number of dimensions for vector similarity.
            The maximum number of supported dimensions is 2000
        num_lists: This integer is the number of clusters that the
            inverted file (IVF) index uses to group the vector data.
            We recommend that numLists is set to documentCount/1000
            for up to 1 million documents and to sqrt(documentCount)
            for more than 1 million documents.
            Using a numLists value of 1 is akin to performing
            brute-force search, which has limited performance
        similarity: Similarity metric to use with the IVF index.
            Possible options are:
                - CosmosDBSimilarityType.COS (cosine distance),
                - CosmosDBSimilarityType.L2 (Euclidean distance), and
                - CosmosDBSimilarityType.IP (inner product).
        collection:
        kind: Type of vector index to create.
            Possible options are:
                - vector-ivf
                - vector-hnsw: available as a preview feature only,
                               to enable visit https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/preview-features
        m: The max number of connections per layer (16 by default, minimum
           value is 2, maximum value is 100). Higher m is suitable for datasets
           with high dimensionality and/or high accuracy requirements.
        ef_construction: the size of the dynamic candidate list for constructing
                        the graph (64 by default, minimum value is 4, maximum
                        value is 1000). Higher ef_construction will result in
                        better index quality and higher accuracy, but it will
                        also increase the time required to build the index.
                        ef_construction has to be at least 2 * m
       ef_search: The size of the dynamic candidate list for search (40 by default).
                  A higher value provides better recall at  the cost of speed.
       database: The Mongo Database object of the azure cosmos db mongo store
    """

    def __init__(
        self,
        collection_name: str,
        index_name: str,
        vector_dimensions: int,
        num_lists: int,
        similarity: CosmosDBSimilarityType,
        kind: CosmosDBVectorSearchType,
        m: int,
        ef_construction: int,
        ef_search: int,
        database=None,
    ):
        """Initializes a new instance of the MongoStoreApi class."""
        self.database = database
        self.collection_name = collection_name
        self.index_name = index_name
        self.num_lists = num_lists
        self.similarity = similarity
        self.vector_dimensions = vector_dimensions
        self.kind = kind
        self.m = m
        self.ef_construction = ef_construction
        self.ef_search = ef_search

    @override
    async def create_collection(self, collection_name: str) -> None:
        if (
            not await self.does_collection_exist(collection_name)
            and self.index_name not in self.database[collection_name].list_indexes()
        ):
            # check the kind of vector search to be performed
            # prepare the command accordingly
            create_index_commands = {}
            if self.kind == CosmosDBVectorSearchType.VECTOR_IVF:
                create_index_commands = self._get_vector_index_ivf(
                    collection_name, self.kind, self.num_lists, self.similarity, self.vector_dimensions
                )
            elif self.kind == CosmosDBVectorSearchType.VECTOR_HNSW:
                create_index_commands = self._get_vector_index_hnsw(
                    collection_name,
                    self.kind,
                    self.m,
                    self.ef_construction,
                    self.similarity,
                    self.vector_dimensions,
                )
            # invoke the command from the database object
            self.database.command(create_index_commands)
        self.collection = self.database[collection_name]

    def _get_vector_index_ivf(
        self, collection_name: str, kind: str, num_lists: int, similarity: str, dimensions: int
    ) -> dict[str, Any]:
        return {
            "createIndexes": collection_name,
            "indexes": [
                {
                    "name": self.index_name,
                    "key": {"embedding": "cosmosSearch"},
                    "cosmosSearchOptions": {
                        "kind": kind,
                        "numLists": num_lists,
                        "similarity": similarity,
                        "dimensions": dimensions,
                    },
                }
            ],
        }

    def _get_vector_index_hnsw(
        self, collection_name: str, kind: str, m: int, ef_construction: int, similarity: str, dimensions: int
    ) -> dict[str, Any]:
        return {
            "createIndexes": collection_name,
            "indexes": [
                {
                    "name": self.index_name,
                    "key": {"embedding": "cosmosSearch"},
                    "cosmosSearchOptions": {
                        "kind": kind,
                        "m": m,
                        "efConstruction": ef_construction,
                        "similarity": similarity,
                        "dimensions": dimensions,
                    },
                }
            ],
        }

    @override
    async def get_collections(self) -> list[str]:
        return self.database.list_collection_names()

    @override
    async def delete_collection(self, collection_name: str) -> None:
        return self.collection.drop()

    @override
    async def does_collection_exist(self, collection_name: str) -> bool:
        return collection_name in self.database.list_collection_names()

    @override
    async def upsert(self, collection_name: str, record: MemoryRecord) -> str:
        result = await self.upsert_batch(collection_name, [record])
        return result[0]

    @override
    async def upsert_batch(self, collection_name: str, records: list[MemoryRecord]) -> list[str]:
        doc_ids: list[str] = []
        cosmosRecords: list[dict] = []
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

    @override
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

    @override
    async def get_batch(self, collection_name: str, keys: list[str], with_embeddings: bool) -> list[MemoryRecord]:
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

    @override
    async def remove(self, collection_name: str, key: str) -> None:
        self.collection.delete_one({"_id": key})

    @override
    async def remove_batch(self, collection_name: str, keys: list[str]) -> None:
        self.collection.delete_many({"_id": {"$in": keys}})

    @override
    async def get_nearest_matches(
        self,
        collection_name: str,
        embedding: np.ndarray,
        limit: int,
        min_relevance_score: float,
        with_embeddings: bool,
    ) -> list[tuple[MemoryRecord, float]]:
        pipeline: list[dict[str, Any]] = []
        if self.kind == CosmosDBVectorSearchType.VECTOR_IVF:
            pipeline = self._get_pipeline_vector_ivf(embedding.tolist(), limit)
        elif self.kind == CosmosDBVectorSearchType.VECTOR_HNSW:
            pipeline = self._get_pipeline_vector_hnsw(embedding.tolist(), limit, self.ef_search)

        cursor = self.collection.aggregate(pipeline)

        nearest_results = []
        # Perform vector search
        for aggResult in cursor:
            score = aggResult["similarityScore"]
            if score < min_relevance_score:
                continue
            result = MemoryRecord.local_record(
                id=aggResult["_id"],
                embedding=np.array(aggResult["document"]["embedding"]) if with_embeddings else np.array([]),
                text=aggResult["document"]["text"],
                description=aggResult["document"]["description"],
                additional_metadata=aggResult["document"]["metadata"],
                timestamp=aggResult["document"].get("timestamp", None),
            )
            nearest_results.append((result, aggResult["similarityScore"]))
        return nearest_results

    def _get_pipeline_vector_ivf(self, embeddings: list[float], k: int = 4) -> list[dict[str, Any]]:
        pipeline: list[dict[str, Any]] = [
            {
                "$search": {
                    "cosmosSearch": {
                        "vector": embeddings,
                        "path": "embedding",
                        "k": k,
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
        return pipeline

    def _get_pipeline_vector_hnsw(
        self, embeddings: list[float], k: int = 4, ef_search: int = 40
    ) -> list[dict[str, Any]]:
        pipeline: list[dict[str, Any]] = [
            {
                "$search": {
                    "cosmosSearch": {
                        "vector": embeddings,
                        "path": "embedding",
                        "k": k,
                        "efSearch": ef_search,
                    },
                }
            },
            {
                "$project": {
                    "similarityScore": {"$meta": "searchScore"},
                    "document": "$$ROOT",
                }
            },
        ]
        return pipeline

    @override
    async def get_nearest_match(
        self,
        collection_name: str,
        embedding: np.ndarray,
        min_relevance_score: float,
        with_embedding: bool,
    ) -> tuple[MemoryRecord, float]:
        nearest_results = await self.get_nearest_matches(
            collection_name=collection_name,
            embedding=embedding,
            min_relevance_score=min_relevance_score,
            with_embeddings=with_embedding,
            limit=1,
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
