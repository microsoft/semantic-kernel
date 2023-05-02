# Copyright (c) Microsoft. All rights reserved.

import pinecone
import json

from typing import Dict, List, Optional, Tuple
from copy import deepcopy
from logging import Logger

from numpy import array, linalg, ndarray

from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.null_logger import NullLogger


class PineconeMemoryStore(MemoryStoreBase):
    _logger: Logger
    _pinecone_api_key: str
    _pinecone_environment: str
    

    def __init__(self, api_key: str, environment: str, logger: Optional[Logger] = None) -> None:
        self._pinecone_api_key = api_key
        self._pinecone_environment = environment
        self._logger = logger or NullLogger()

        """Initializes a new instance of the PineconeMemoryStore class.

        Arguments:
            pinecone_api_key {str} -- The Pinecone API key.
            pinecone_environment {str} -- The Pinecone environment key/type.
            logger {Optional[Logger]} -- The logger to use. (default: {None})
        """

        pinecone.init(api_key=self._pinecone_api_key, environment=self._pinecone_environment)
         
    async def create_collection_async(
            self,
            collection_name: str,
            dimension_num: int,
            distance_type: Optional[str] = "cosine",
            num_of_pods: Optional[int] = 1,
            replica_num: Optional[int] = 0,
            type_of_pod: Optional[str]="p1.x1") -> None:
        """Creates a new collection in Pinecone if it does not exist.
            This function creates an index without a metadata configuration using the
            Pinecone default to index all metadata.

        Arguments:
            collection_name {str} -- The name of the collection to create. 
            In Pinecone, a collection is represented as an index. The concept
            of "collection" in Pinecone is just a static copy of an index. 
            dimension {int} -- The dimension of the embeddings in the collection.

        Returns:
            None
        """

        if collection_name in pinecone.list_indexes():
            pass
        else:
            pinecone.create_index(name=collection_name, 
                    dimension=dimension_num, 
                      metric=distance_type, 
                      pods=num_of_pods, 
                      replicas=replica_num, 
                      pod_type=type_of_pod)
            
    async def get_collections_async(
        self,
    ) -> List[str]:
        """Gets the list of collections.

        Returns:
            List[str] -- The list of collections.
        """
        return list(pinecone.list_indexes())

    async def delete_collection_async(self, collection_name: str) -> None:
        """Deletes a collection.

        Arguments:
            collection_name {str} -- The name of the collection to delete.

        Returns:
            None
        """
        if collection_name in pinecone.list_indexes():
            pinecone.delete_index(collection_name)

    async def does_collection_exist_async(self, collection_name: str) -> bool:
        """Checks if a collection exists.

        Arguments:
            collection_name {str} -- The name of the collection to check.

        Returns:
            bool -- True if the collection exists; otherwise, False.
        """
        return collection_name in pinecone.list_indexes()

    async def upsert_async(self, collection_name: str, record: MemoryRecord) -> str:
        """Upserts a record.

        Arguments:
            collection_name {str} -- The name of the collection to upsert the record into.
            record {MemoryRecord} -- The record to upsert.

        Returns:
            str -- The unqiue database key of the record. In Pinecone, this is the record ID.
        """
        if collection_name not in pinecone.list_indexes():
            raise Exception(f"Collection '{collection_name}' does not exist")
        
        collection = pinecone.Index(collection_name)

        metadata_info = json.dumps(record._metadata)

        upsert_response = collection.upsert(
            vectors=[
                {
                'id':record._id, 
                'values':record._embedding, 
                'metadata':metadata_info,
                },
            ],
            namespace=''
        )

        if upsert_response.upsertedCount == None:
            raise Exception(f"Error upserting record: {upsert_response.text}")
        
        return record._id



    async def upsert_batch_async(
        self, collection_name: str, records: List[MemoryRecord]
    ) -> List[str]:
        """Upserts a batch of records.

        Arguments:
            collection_name {str} -- The name of the collection to upsert the records into.
            records {List[MemoryRecord]} -- The records to upsert.

        Returns:
            List[str] -- The unqiue database keys of the records.
        """
        if collection_name not in pinecone.list_indexes():
            raise Exception(f"Collection '{collection_name}' does not exist")

        for record in records:
            upsert_response = collection.upsert(
            vectors=[
                {
                'id':record._id, 
                'values':record._embedding, 
                'metadata':metadata_info,
                },
            ],
            namespace=''
        )

            if upsert_response.upsertedCount == None:
                raise Exception(f"Error upserting record: {upsert_response.text}")
            else:
                return [record._id for record in records]

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
        if collection_name not in pinecone.list_indexes():
            raise Exception(f"Collection '{collection_name}' does not exist")

        collection_info = pinecone.describe_index(collection_name)
        collection = pinecone.Index(collection_name) 

        result = MemoryRecord(id=collection_info['id'])

        if not with_embedding:
            # create copy of results without embeddings
            result = deepcopy(result)
            result._embedding = None

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
        if collection_name not in self._store:
            raise Exception(f"Collection '{collection_name}' does not exist")

        results = [
            self._store[collection_name][key]
            for key in keys
            if key in self._store[collection_name]
        ]

        if not with_embeddings:
            # create copy of results without embeddings
            for result in results:
                result = deepcopy(result)
                result._embedding = None
        return results

    async def remove_async(self, collection_name: str, key: str) -> None:
        """Removes a record.

        Arguments:
            collection_name {str} -- The name of the collection to remove the record from.
            key {str} -- The unique database key of the record to remove.

        Returns:
            None
        """
        if collection_name not in pinecone.list_indexes():
            raise Exception(f"Collection '{collection_name}' does not exist")

        pinecone.delete_index(collection_name)

    async def remove_batch_async(self, collection_name: str, keys: List[str]) -> None:
        """Removes a batch of records.

        Arguments:
            collection_name {str} -- The name of the collection to remove the records from.
            keys {List[str]} -- The unique database keys of the records to remove.

        Returns:
            None
        """
        if collection_name not in pinecone.list_indexes():
            raise Exception(f"Collection '{collection_name}' does not exist")

        for key in keys:
            if key in self._store[collection_name]:
                del self._store[collection_name][key]

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
        collection = pinecone.Index(collection_name)

        responses = collection.query(embedding, top_k=1, include_metadata=True)

        record = MemoryRecord(id=responses[0].id, embedding=responses[0].values)
        result = (record, responses[0].score)

        return result

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
        if collection_name not in self._store:
            return []

        # Get all the records in the collection
        memory_records = list(self._store[collection_name].values())

        # Convert the collection of embeddings into a numpy array (stacked)
        embeddings = array([x._embedding for x in memory_records], dtype=float)
        embeddings = embeddings.reshape(embeddings.shape[0], -1)

        # If the query embedding has shape (1, embedding_size),
        # reshape it to (embedding_size,)
        if len(embedding.shape) == 2:
            embedding = embedding.reshape(
                embedding.shape[1],
            )

        # Use numpy to get the cosine similarity between the query
        # embedding and all the embeddings in the collection
        similarity_scores = self.compute_similarity_scores(embedding, embeddings)

        # Then, sort the results by the similarity score
        sorted_results = sorted(
            zip(memory_records, similarity_scores),
            key=lambda x: x[1],
            reverse=True,
        )

        # Then, filter out the results that are below the minimum relevance score
        filtered_results = [x for x in sorted_results if x[1] >= min_relevance_score]

        # Then, take the top N results
        top_results = filtered_results[:limit]

        if not with_embeddings:
            # create copy of results without embeddings
            for result in top_results:
                result = deepcopy(result)
                result[0]._embedding = None
        return top_results

    def compute_similarity_scores(
        self, embedding: ndarray, embedding_array: ndarray
    ) -> ndarray:
        """Computes the cosine similarity scores between a query embedding and a group of embeddings.

        Arguments:
            embedding {ndarray} -- The query embedding.
            embedding_array {ndarray} -- The group of embeddings.

        Returns:
            ndarray -- The cosine similarity scores.
        """
        query_norm = linalg.norm(embedding)
        collection_norm = linalg.norm(embedding_array, axis=1)

        # Compute indices for which the similarity scores can be computed
        valid_indices = (query_norm != 0) & (collection_norm != 0)

        # Initialize the similarity scores with -1 to distinguish the cases
        # between zero similarity from orthogonal vectors and invalid similarity
        similarity_scores = array([-1.0] * embedding_array.shape[0])

        if valid_indices.any():
            similarity_scores[valid_indices] = embedding.dot(
                embedding_array[valid_indices].T
            ) / (query_norm * collection_norm[valid_indices])
            if not valid_indices.all():
                self._logger.warning(
                    "Some vectors in the embedding collection are zero vectors."
                    "Ignoring cosine similarity score computation for those vectors."
                )
        else:
            raise ValueError(
                f"Invalid vectors, cannot compute cosine similarity scores"
                f"for zero vectors"
                f"{embedding_array} or {embedding}"
            )
        return similarity_scores
