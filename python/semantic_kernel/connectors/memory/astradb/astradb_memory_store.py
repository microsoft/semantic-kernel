# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import List, Optional, Tuple
import requests
import json

from numpy import ndarray

from semantic_kernel.connectors.memory.astradb.utils import (
    build_payload,
    parse_payload,
)
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.null_logger import NullLogger

# Limitations set by Pinecone at https://docs.pinecone.io/docs/limits
MAX_DIMENSIONALITY = 20000
MAX_UPSERT_BATCH_SIZE = 100
MAX_QUERY_WITHOUT_METADATA_BATCH_SIZE = 10000
MAX_QUERY_WITH_METADATA_BATCH_SIZE = 1000
MAX_FETCH_BATCH_SIZE = 1000
MAX_DELETE_BATCH_SIZE = 1000


class AstraDBMemoryStore(MemoryStoreBase):
    """A memory store that uses Pinecone as the backend."""

    _logger: Logger
    _request_url: str
    _request_header: str
    _default_dimensionality: int

    def __init__(
        self,
        app_token: str,
        db_id: str,
        region: str,
        keyspace: str,
        default_dimensionality: int,
        logger: Optional[Logger] = None,
    ) -> None:
        """Initializes a new instance of the AstraDBMemoryStore class.

        Arguments:
            app_token {str} -- The Astra application token.
            db_id {str} -- The Astra id of database.
            regin {str} -- The Astra region
            keyspace {str} -- The Astra keyspace
            default_dimensionality {int} -- The default dimensionality to use for new collections.
            logger {Optional[Logger]} -- The logger to use. (default: {None})
        """
        if default_dimensionality > MAX_DIMENSIONALITY:
            raise ValueError(
                f"Dimensionality of {default_dimensionality} exceeds "
                + f"the maximum allowed value of {MAX_DIMENSIONALITY}."
            )

        self._request_url = f"https://{db_id}-{region}.apps.astra.datastax.com/api/json/v1/{keyspace}"
        self._request_header = {
            "x-cassandra-token": app_token,
            "Content-Type": "application/json",
        }
        self._logger = logger or NullLogger()

    def get_collections_async(self) -> List[str]:
        """Gets the list of collections.

        Returns:
            List[str] -- The list of collections.
        """
        find_query = {"findCollections": {"options": {"explain": True}}}
        response = requests.request(
            "POST", self._request_url, headers=self._request_header, data=json.dumps(find_query))
        response_dict = json.loads(response.text)

        if response.status_code == 200:
            if "status" in response_dict:
                return [collection["name"] for collection in response_dict["status"]["collections"]]
            else:
                raise Exception(f"status not in response: {response.text}")

        else:
            raise Exception(
                f"Astra DB not available. Status code: {response.status_code}, {response.text}")

    async def create_collection_async(
        self,
        collection_name: str,
        dimension_num: Optional[int] = None,
        distance_type: Optional[str] = "cosine",
    ) -> None:
        """Creates a new collection in Astra if it does not exist.

        Arguments:
            collection_name {str} -- The name of the collection to create.
            dimension_num {int} -- The dimension of the vectors to be stored in this collection.
            distance_type {str} -- Specifies the similarity metric to be used when querying or comparing vectors within this collection. The available options are dot_product, euclidean, and cosine.
        Returns:
            None
        """
        if dimension_num is None:
            dimension_num = self._default_dimensionality
        if dimension_num > MAX_DIMENSIONALITY:
            raise ValueError(
                f"Dimensionality of {dimension_num} exceeds "
                + f"the maximum allowed value of {MAX_DIMENSIONALITY}."
            )

        create_query = {
            "createCollection": {
                "name": collection_name,
                "options": {"vector": {"dimension": dimension_num, "metric": distance_type}},
            }
        }
        response = requests.request(
            "POST", self._request_url, headers=self._request_header, data=json.dumps(create_query))
        response_dict = json.loads(response.text)
        if response.status_code == 200 and "status" in response_dict:
            self._logger.info(
                f"Collection {collection_name} created: {response.text}")
        else:
            raise Exception(
                f"Create Astra collection ailed with the following error: status code {response.status_code}, {response.text}"
            )

    async def delete_collection_async(self, collection_name: str) -> None:
        """Deletes a collection.

        Arguments:
            collection_name {str} -- The name of the collection to delete.

        Returns:
            None
        """
        collections = self.get_collections()
        collection_name_matches = list(
            filter(lambda d: d == collection_name, collections))
        if len(collection_name_matches) == 0:
            self._logger.warning(
                f"Astra collection {collection_name} not found")
        else:
            delete_query = {
                "deleteCollection": {
                    "name": collection_name,
                }
            }
            response = requests.request(
                "POST", self._request_url, headers=self._request_header, data=json.dumps(delete_query))
            if response.status_code == 200:
                self._logger.info(f"Collection {collection_name} deleted")
            else:
                raise Exception(
                    f"Delete Astra collection ailed with the following error: status code {response.status_code}, {response.text}"
                )

    async def does_collection_exist_async(self, collection_name: str) -> bool:
        """Checks if a collection exists.

        Arguments:
            collection_name {str} -- The name of the collection to check.

        Returns:
            bool -- True if the collection exists; otherwise, False.
        """
        collections = self.get_collections_async()
        return collection_name in collections

    async def upsert_async(self, collection_name: str, record: MemoryRecord) -> str:
        query = json.dumps({"insertOne": {"document": build_payload(record)}})
        response = requests.request(
            "POST",
            f"{self._request_url}/{collection_name}",
            headers=self._request_header,
            data=query,
        )
        response_dict = json.loads(response.text)

        if response.status_code == 200:
            if "status" in response_dict and "insertedIds" in response_dict["status"]:
                return response_dict["status"]["insertedIds"][0]
            else:
                if "errors" in response_dict:
                    self._logger.error(response_dict["errors"])
        else:
            raise Exception(
                f"Astra DB request error - status code: {response.status_code} response {response.text}")

    async def upsert_batch_async(
        self, collection_name: str, records: List[MemoryRecord]
    ) -> List[str]:
        documents = [build_payload(record) for record in records]

        query = json.dumps(
            {"insertMany": {"options": {"ordered": False}, "documents": documents}})

        response = requests.request(
            "POST",
            f"{self._request_url}/{collection_name}",
            headers=self._request_header,
            data=query,
        )
        response_dict = json.loads(response.text)
        if response.status_code == 200:
            if "status" in response_dict and "insertedIds" in response_dict["status"]:
                return response_dict["status"]["insertedIds"]
            else:
                if "errors" in response_dict:
                    self._logger.error(response_dict["errors"])
                return []
        else:
            raise Exception(
                f"Astra DB request error - status code: {response.status_code} response {response.text}")

    async def get_async(
        self, collection_name: str, key: str, with_embedding: bool = False
    ) -> MemoryRecord:
        """Gets a record. Does not guarantee that the collection exists.

        Arguments:
            collection_name {str} -- The name of the collection to get the record from.
            key {str} -- The unique database key of the record.
            with_embedding {bool} -- Whether to include the embedding in the result. (default: {False})

        Returns:
            MemoryRecord -- The record.
        """
        query = json.dumps({"findOne": {"filter": {"_id": key}}})
        response = requests.request(
            "POST",
            f"{self._request_url}/{collection_name}",
            headers=self._request_header,
            data=query,
        )
        response_dict = json.loads(response.text)
        if response.status_code == 200:
            if "data" in response_dict and "document" in response_dict["data"]:
                return parse_payload(response_dict["data"]["document"])
            else:
                raise KeyError(f"Record with key '{key}' does not exist")
        else:
            raise Exception(
                f"Astra DB request error - status code: {response.status_code} response {response.text}")

    async def get_batch_async(
        self, collection_name: str, keys: List[str], with_embeddings: bool = False
    ) -> List[MemoryRecord]:
        """Gets a batch of records. Does not guarantee that the collection exists.

        Arguments:
            collection_name {str} -- The name of the collection to get the records from.
            keys {List[str]} -- The unique database keys of the records.
            with_embeddings {bool} -- Whether to include the embeddings in the results. (default: {False})

        Returns:
            List[MemoryRecord] -- The records.
        """
        query = json.dumps({"find": {"filter": {"_id": {"$in": keys}}}})
        response = requests.request(
            "POST",
            f"{self._request_url}/{collection_name}",
            headers=self._request_header,
            data=query,
        )
        response_dict = json.loads(response.text)
        if response.status_code == 200:
            if "data" in response_dict and "documents" in response_dict["data"]:
                return [parse_payload(document) for document in response_dict["data"]["documents"]]
            else:
                return []
        else:
            raise Exception(
                f"Astra DB request error - status code: {response.status_code} response {response.text}")

    async def remove_async(self, collection_name: str, key: str) -> None:
        """Removes a memory record from the data store. Does not guarantee that the collection exists.

        Arguments:
            collection_name {str} -- The name of the collection to remove the record from.
            key {str} -- The unique id associated with the memory record to remove.

        Returns:
            None
        """
        query = json.dumps({"deleteOne": {"filter": {"_id": key}}})
        response = requests.request(
            "POST",
            f"{self._request_url}/{collection_name}",
            headers=self._request_header,
            data=query,
        )
        response_dict = json.loads(response.text)
        if response.status_code == 200:
            if "status" in response_dict and "deletedCount" in response_dict["status"]:
                self._logger.info(
                    f"Remove {response_dict.status.deletedCount}")
            else:
                if "errors" in response_dict:
                    self._logger.error(response_dict["errors"])
        else:
            raise Exception(
                f"Astra DB request error - status code: {response.status_code} response {response.text}")

    async def remove_batch_async(self, collection_name: str, keys: List[str]) -> None:
        """Removes a batch of records. Does not guarantee that the collection exists.

        Arguments:
            collection_name {str} -- The name of the collection to remove the records from.
            keys {List[str]} -- The unique ids associated with the memory records to remove.

        Returns:
            None
        """
        query = json.dumps({"deleteMany": {"filter": {"_id": {"$in": keys}}}})
        response = requests.request(
            "POST",
            f"{self._request_url}/{collection_name}",
            headers=self._request_header,
            data=query,
        )
        response_dict = json.loads(response.text)
        if response.status_code == 200:
            if "status" in response_dict and "deletedCount" in response_dict["status"]:
                self._logger.info(
                    f"Remove {response_dict['status']['deletedCount']}")
            else:
                if "errors" in response_dict:
                    self._logger.error(response_dict["errors"])
        else:
            raise Exception(
                f"Astra DB request error - status code: {response.status_code} response {response.text}")

    async def get_nearest_match_async(
        self,
        collection_name: str,
        embedding: ndarray,
        min_relevance_score: float = 0.0,
        with_embedding: bool = False,
    ) -> Tuple[MemoryRecord, float]:
        """Gets the nearest match to an embedding using cosine similarity.
        Arguments:
            collection_name {str} -- The name of the collection to get the nearest matches from.
            embedding {ndarray} -- The embedding to find the nearest matches to.
            min_relevance_score {float} -- The minimum relevance score of the matches. (default: {0.0})
            with_embeddings {bool} -- Whether to include the embeddings in the results. (default: {False})

        Returns:
            List[Tuple[MemoryRecord, float]] -- The records and their relevance scores.
        """
        matches = await self.get_nearest_matches_async(
            collection_name=collection_name,
            embedding=embedding,
            limit=1,
            min_relevance_score=min_relevance_score,
            with_embeddings=with_embedding,
        )
        return matches[0]

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
        query = json.dumps({
            "find": {
                "sort": {"$vector": embedding.tolist()},
                "projection": {
                    "$vector": with_embeddings
                },
                "options": {
                    "includeSimilarity": True,
                    "limit": limit,
                }
            }
        })
        response = requests.request(
            "POST",
            f"{self._request_url}/{collection_name}",
            headers=self._request_header,
            data=query,
        )
        response_dict = json.loads(response.text)

        matches = response_dict["data"]["documents"]
        if min_relevance_score:
            matches = [
                match for match in matches if match["$similarity"] >= min_relevance_score]

        return (
            [
                (
                    parse_payload(match),
                    match["$similarity"],
                )
                for match in matches
            ]
            if len(matches) > 0
            else []
        )
