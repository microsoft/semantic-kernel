# Import required libraries

import os
import json
from typing import List, Optional, Tuple
from dotenv import load_dotenv
from logging import Logger, NullLogger

from numpy import ndarray
from python.semantic_kernel.connectors.memory.azure_cog_search.acs_utils import (
    create_credentials,
)

from tenacity import retry, wait_random_exponential, stop_after_attempt
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.models import Vector, QueryType
from azure.identity import DefaultAzureCredential as DefaultAzureCredentialSync
from azure.identity.aio import DefaultAzureCredential
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    SemanticConfiguration,
    PrioritizedFields,
    SemanticField,
    SemanticSettings,
    VectorSearch,
    VectorSearchAlgorithmConfiguration,
)
from python.semantic_kernel.memory.memory_record import MemoryRecord

from python.semantic_kernel.memory.memory_store_base import MemoryStoreBase


class CognitiveSearchMemoryStore(MemoryStoreBase):
    _cogsearch_indexclient: SearchIndexClient
    _cogsearch_client: SearchClient
    _cogsearch_records: list
    _cogsearch_creds: AzureKeyCredential
    _logger: Logger

    def __init__(
        self,
        acs_endpoint: str,
        acs_credential: Optional[AzureKeyCredential] = None,
        acs_search_key: Optional[str] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        """Initializes a new instance of the CogintiveSearchMemoryStore class.

        Arguments:
            endpoint {str} -- The endpoint of the CogintiveSearch service.
            logger {Optional[Logger]} -- The logger to use. (default: {None})
        """
        try:
            from azure.search.documents.indexes import SearchIndexClient
        except ImportError:
            raise ValueError(
                "Error: Unable to import azure cognitive search client python package."
                "Please install azure cognitive search client"
            )

        # Configure environment variables
        load_dotenv()

        self._cogsearch_creds = create_credentials(
            use_async=True, azsearch_api_key=acs_search_key
        )

        # Override environment variable with endpoint provided
        if acs_endpoint:
            service_endpoint = acs_endpoint
        else:
            service_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")

        self._cogsearch_indexclient = SearchIndexClient(
            endpoint=service_endpoint, credential=self._cogsearch_creds
        )

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

        fields = [
            SimpleField(
                name="collection_id", type=SearchFieldDataType.String, key=True
            ),
            SearchableField(
                name="collection_name",
                type=SearchFieldDataType.String,
                searchable=True,
                retrievable=True,
            ),
            SearchableField(
                name="content",
                type=SearchFieldDataType.String,
                searchable=True,
                retrievable=True,
            ),
            SearchableField(
                name="payload",
                type=SearchFieldDataType.String,
                filterable=True,
                searchable=True,
                retrievable=True,
            ),
            SearchField(
                name="titleVector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                dimensions=1536,
                vector_search_configuration="vector-config",
            ),
            SearchField(
                name="contentVector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                dimensions=1536,
                vector_search_configuration="vector-config",
            ),
        ]

        vector_search = VectorSearch(
            algorithm_configurations=[
                VectorSearchAlgorithmConfiguration(
                    name="az-vector-config",
                    kind="hnsw",
                    hnsw_parameters={
                        "m": 4,
                        "efConstruction": 400,
                        "efSearch": 500,
                        "metric": "cosine",
                    },
                )
            ]
        )

        semantic_config = SemanticConfiguration(
            name="az-semantic-config",
            prioritized_fields=PrioritizedFields(
                title_field=SemanticField(field_name="collection_name"),
                prioritized_keywords_fields=[SemanticField(field_name="vector")],
                prioritized_content_fields=[SemanticField(field_name="payload")],
            ),
        )

        # Create the semantic settings with the configuration
        semantic_settings = SemanticSettings(configurations=[semantic_config])

        # Create the search index with the semantic settings
        index = SearchIndex(
            name=collection_name,
            fields=fields,
            vector_search=vector_search,
            semantic_settings=semantic_settings,
        )

        result = self._cogsearch_indexclient.create_index(index)

    async def get_collections_async(
        self,
    ) -> List[str]:
        """Gets the list of collections.

        Returns:
            List[str] -- The list of collections.
        """
        return list(self._cogsearch_indexclient.get_collections())

    async def get_collection(self, collection_name: str) -> CollectionInfo:
        """Gets the a collections based upon collection name.

        Returns:
            CollectionInfo -- Collection Information from Qdrant about collection.
        """
        collection_info = self._cogsearch_indexclient.get_collection(
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
        self._cogsearch_indexclient.delete_index(index=collection_name)

    async def does_collection_exist_async(self, collection_name: str) -> bool:
        """Checks if a collection exists.

        Arguments:
            collection_name {str} -- The name of the collection to check.

        Returns:
            bool -- True if the collection exists; otherwise, False.
        """

        collection_info = self._cogsearch_indexclient.get_collection(
            collection_name=collection_name
        )

        if collection_info.status == CollectionStatus.GREEN:
            return collection_name
        else:
            return ""

    async def upsert_async(self, collection_name: str, record: MemoryRecord) -> str:
        """Upserts a record.

        Arguments:
            collection_name {str} -- The name of the collection to upsert the record into.
            record {MemoryRecord} -- The record to upsert.

        Returns:
            str -- The unique database key of the record.
        """
        record._key = record._id

        collection_info = self.does_collection_exist_async(
            collection_name=collection_name
        )

        if not collection_info:
            raise Exception(f"Collection '{collection_name}' does not exist")

        upsert_info = self._cogsearch_indexclient.upsert(
            collection_name=collection_name,
            wait=True,
            points=[
                PointStruct(
                    id=record._key, vector=record._embedding, payload=record._payload
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
            record._key = record._id
            pointstruct = PointStruct(
                id=record._id, vector=record._embedding, payload=record._payload
            )
            points_rec.append([pointstruct])
            upsert_info = self._cogsearch_indexclient.upsert(
                collection_name=collection_name, wait=True, points=points_rec
            )

        if upsert_info.status == UpdateStatus.COMPLETED:
            return [record._key for record in records]
        else:
            return ""

    async def get_async(
        self, collection_name: str, key: str, with_embedding: bool = True
    ) -> MemoryRecord:
        """Gets a record.

        Arguments:
            collection_name {str} -- The name of the collection to get the record from.
            key {str} -- The unique database key of the record.
            with_embedding {bool} -- Whether to include the embedding in the result. (default: {False})

        Returns:
            MemoryRecord -- The record.
        """

        search_id = key

        results = self._cogsearch_client.search(
            search_text="",
            vector=Vector(value=search_id, k=3, fields="collection_id"),
            select=["collection_id", "vector", "payload"],
        )

        result = MemoryRecord(
            is_reference=False,
            external_source_name="azure-cognitive-search",
            key=search_id,
            id=search_id,
            embedding=results[0].vector,
            payload=results[0].payload,
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

        acs_results = List[MemoryRecord]

        for acs_key in keys:
            results = self._cogsearch_client.search(
                search_text="",
                vector=Vector(value=acs_key, k=3, fields="collection_id"),
                select=["collection_id", "vector", "payload"],
            )

            result = MemoryRecord(
                is_reference=False,
                external_source_name="azure-cognitive-search",
                key=acs_key,
                id=acs_key,
                embedding=results[0].vector,
                payload=results[0].payload,
            )

            acs_results.append(result)

        return acs_results

    async def remove_async(self, collection_name: str, key: str) -> None:
        """Removes a record.

        Arguments:
            collection_name {str} -- The name of the collection to remove the record from.
            key {str} -- The unique database key of the record to remove.

        Returns:
            None
        """
        self._cogsearch_indexclient.delete_index(index=collection_name)

    async def remove_batch_async(self, collection_name: str, keys: List[str]) -> None:
        """Removes a batch of records.

        Arguments:
            collection_name {str} -- The name of the collection to remove the records from.
            keys {List[str]} -- The unique database keys of the records to remove.

        Returns:
            None
        """
        collection_info = self._cogsearch_indexclient.get_collection(
            collection_name=collection_name
        )

        if not collection_info.status == CollectionStatus.GREEN:
            raise Exception(f"Collection '{collection_name}' does not exist")

        self._cogsearch_indexclient.delete(
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

        if with_embeddings:
            select_fields = ["collection_id", "vector", "payload"]
        else:
            select_fields = ["collection_id", "payload"]

        results = self._cogsearch_client.search(
            search_text=collection_name,
            vector=Vector(value=embedding, k=3, fields="vector"),
            select=select_fields,
            top=limit,
        )

        nearest_results = []

        # Convert the results to MemoryRecords
        for acs_result in results:
            vector_result = MemoryRecord(
                is_reference=False,
                external_source_name="azure-cognitive-search",
                key=None,
                id=acs_result.collection_id,
                embedding=acs_result.vector,
                payload=acs_result.payload,
            )

            nearest_results.append(tuple(vector_result, acs_result.score))

        return nearest_results
