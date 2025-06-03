# Copyright (c) Microsoft. All rights reserved.

import contextlib
import logging
import uuid
from inspect import isawaitable

from azure.core.credentials import AzureKeyCredential, TokenCredential
from azure.core.exceptions import ResourceNotFoundError
from azure.search.documents.indexes.aio import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    HnswParameters,
    SearchIndex,
    SearchResourceEncryptionKey,
    VectorSearch,
    VectorSearchProfile,
)
from azure.search.documents.models import VectorizedQuery
from numpy import ndarray
from pydantic import ValidationError

from semantic_kernel.connectors.memory.azure_cognitive_search.utils import (
    SEARCH_FIELD_EMBEDDING,
    SEARCH_FIELD_ID,
    dict_to_memory_record,
    encode_id,
    get_field_selection,
    get_index_schema,
    get_search_index_async_client,
    memory_record_to_search_record,
)
from semantic_kernel.exceptions import MemoryConnectorInitializationError, MemoryConnectorResourceNotFound
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.feature_stage_decorator import experimental

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class AzureCognitiveSearchMemoryStore(MemoryStoreBase):
    """Azure Cognitive Search Memory Store."""

    _search_index_client: SearchIndexClient = None
    _vector_size: int = None

    def __init__(
        self,
        vector_size: int,
        search_endpoint: str | None = None,
        admin_key: str | None = None,
        azure_credentials: AzureKeyCredential | None = None,
        token_credentials: TokenCredential | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initializes a new instance of the AzureCognitiveSearchMemoryStore class.

        Instantiate using Async Context Manager:
            async with AzureCognitiveSearchMemoryStore(<...>) as memory:
                await memory.<...>

        Args:
            vector_size (int): Embedding vector size.
            search_endpoint (str | None): The endpoint of the Azure Cognitive Search service
                (default: {None}).
            admin_key (str | None): Azure Cognitive Search API key (default: {None}).
            azure_credentials (AzureKeyCredential | None): Azure Cognitive Search credentials (default: {None}).
            token_credentials (TokenCredential | None): Azure Cognitive Search token credentials
                (default: {None}).
            env_file_path (str | None): Use the environment settings file as a fallback
                to environment variables
            env_file_encoding (str | None): The encoding of the environment settings file

        """
        from semantic_kernel.connectors.memory.azure_cognitive_search.azure_ai_search_settings import (
            AzureAISearchSettings,
        )

        try:
            acs_memory_settings = AzureAISearchSettings(
                env_file_path=env_file_path,
                endpoint=search_endpoint,
                api_key=admin_key,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as exc:
            raise MemoryConnectorInitializationError("Failed to create Azure Cognitive Search settings.") from exc

        self._vector_size = vector_size
        self._search_index_client = get_search_index_async_client(
            search_endpoint=str(acs_memory_settings.endpoint),
            admin_key=acs_memory_settings.api_key.get_secret_value() if acs_memory_settings.api_key else None,
            azure_credential=azure_credentials,
            token_credential=token_credentials,
        )

    async def close(self):
        """Async close connection, invoked by MemoryStoreBase.__aexit__()."""
        if self._search_index_client is not None:
            await self._search_index_client.close()

    async def create_collection(
        self,
        collection_name: str,
        vector_config: HnswAlgorithmConfiguration | None = None,
        search_resource_encryption_key: SearchResourceEncryptionKey | None = None,
    ) -> None:
        """Creates a new collection if it does not exist.

        Args:
            collection_name (str): The name of the collection to create.
            vector_config (HnswVectorSearchAlgorithmConfiguration): Optional search algorithm configuration
                                                                      (default: {None}).
            semantic_config (SemanticConfiguration): Optional search index configuration (default: {None}).
            search_resource_encryption_key (SearchResourceEncryptionKey): Optional Search Encryption Key
                                                                                       (default: {None}).

        Returns:
            None
        """
        vector_search_profile_name = "az-vector-config"
        if vector_config:
            vector_search_profile = VectorSearchProfile(
                name=vector_search_profile_name, algorithm_configuration_name=vector_config.name
            )
            vector_search = VectorSearch(profiles=[vector_search_profile], algorithms=[vector_config])
        else:
            vector_search_algorithm_name = "az-vector-hnsw-config"
            vector_search_profile = VectorSearchProfile(
                name=vector_search_profile_name, algorithm_configuration_name=vector_search_algorithm_name
            )
            vector_search = VectorSearch(
                profiles=[vector_search_profile],
                algorithms=[
                    HnswAlgorithmConfiguration(
                        name=vector_search_algorithm_name,
                        kind="hnsw",
                        parameters=HnswParameters(
                            m=4,  # Number of bidirectional links, typically between 4 and 10
                            ef_construction=400,  # Size during indexing, range: 100-1000
                            ef_search=500,  # Size during search, range: 100-1000
                            metric="cosine",  # Can be "cosine", "dotProduct", or "euclidean_distance"
                        ),
                    )
                ],
            )

        if not self._search_index_client:
            raise MemoryConnectorInitializationError("Error: self._search_index_client not set 1.")

        # Check to see if collection exists
        collection_index = None
        with contextlib.suppress(ResourceNotFoundError):
            collection_index = await self._search_index_client.get_index(collection_name.lower())

        if not collection_index:
            # Create the search index with the semantic settings
            index = SearchIndex(
                name=collection_name.lower(),
                fields=get_index_schema(self._vector_size, vector_search_profile_name),
                vector_search=vector_search,
                encryption_key=search_resource_encryption_key,
            )

            await self._search_index_client.create_index(index)

    async def get_collections(self) -> list[str]:
        """Gets the list of collections.

        Returns:
            List[str]: The list of collections.
        """
        results_list = []
        items = self._search_index_client.list_index_names()
        if isawaitable(items):
            items = await items

        async for result in items:
            results_list.append(result)

        return results_list

    async def delete_collection(self, collection_name: str) -> None:
        """Deletes a collection.

        Args:
            collection_name (str): The name of the collection to delete.

        Returns:
            None
        """
        await self._search_index_client.delete_index(index=collection_name.lower())

    async def does_collection_exist(self, collection_name: str) -> bool:
        """Checks if a collection exists.

        Args:
            collection_name (str): The name of the collection to check.

        Returns:
            bool: True if the collection exists; otherwise, False.
        """
        try:
            collection_result = await self._search_index_client.get_index(name=collection_name.lower())

            return bool(collection_result)
        except ResourceNotFoundError:
            return False

    async def upsert(self, collection_name: str, record: MemoryRecord) -> str:
        """Upsert a record.

        Args:
            collection_name (str): The name of the collection to upsert the record into.
            record (MemoryRecord): The record to upsert.

        Returns:
            str: The unique record id of the record.
        """
        result = await self.upsert_batch(collection_name, [record])
        if result:
            return result[0]
        return None

    async def upsert_batch(self, collection_name: str, records: list[MemoryRecord]) -> list[str]:
        """Upsert a batch of records.

        Args:
            collection_name (str): The name of the collection to upsert the records into.
            records (List[MemoryRecord]): The records to upsert.

        Returns:
            List[str]: The unique database keys of the records.
        """
        # Initialize search client here
        # Look up Search client class to see if exists or create
        search_client = self._search_index_client.get_search_client(collection_name.lower())

        search_records = []
        search_ids = []

        for record in records:
            # Note:
            # * Document id     = user provided value
            # * MemoryRecord.id = base64(Document id)
            if not record._id:
                record._id = str(uuid.uuid4())

            search_record = memory_record_to_search_record(record)
            search_records.append(search_record)
            search_ids.append(record._id)

        result = await search_client.upload_documents(documents=search_records)
        await search_client.close()

        if result[0].succeeded:
            return search_ids
        return None

    async def get(self, collection_name: str, key: str, with_embedding: bool = False) -> MemoryRecord:
        """Gets a record.

        Args:
            collection_name (str): The name of the collection to get the record from.
            key (str): The unique database key of the record.
            with_embedding (bool): Whether to include the embedding in the result. (default: {False})

        Returns:
            MemoryRecord: The record.
        """
        # Look up Search client class to see if exists or create
        search_client = self._search_index_client.get_search_client(collection_name.lower())

        try:
            search_result = await search_client.get_document(
                key=encode_id(key), selected_fields=get_field_selection(with_embedding)
            )
        except ResourceNotFoundError as exc:
            await search_client.close()
            raise MemoryConnectorResourceNotFound("Memory record not found") from exc

        await search_client.close()

        # Create Memory record from document
        return dict_to_memory_record(search_result, with_embedding)

    async def get_batch(
        self, collection_name: str, keys: list[str], with_embeddings: bool = False
    ) -> list[MemoryRecord]:
        """Gets a batch of records.

        Args:
            collection_name (str): The name of the collection to get the records from.
            keys (List[str]): The unique database keys of the records.
            with_embeddings (bool): Whether to include the embeddings in the results. (default: {False})

        Returns:
            List[MemoryRecord]: The records.
        """
        search_results = []

        for key in keys:
            search_result = await self.get(
                collection_name=collection_name.lower(),
                key=key,
                with_embedding=with_embeddings,
            )
            search_results.append(search_result)

        return search_results

    async def remove_batch(self, collection_name: str, keys: list[str]) -> None:
        """Removes a batch of records.

        Args:
            collection_name (str): The name of the collection to remove the records from.
            keys (List[str]): The unique database keys of the records to remove.

        Returns:
            None
        """
        for record_id in keys:
            await self.remove(collection_name=collection_name.lower(), key=encode_id(record_id))

    async def remove(self, collection_name: str, key: str) -> None:
        """Removes a record.

        Args:
            collection_name (str): The name of the collection to remove the record from.
            key (str): The unique database key of the record to remove.

        Returns:
            None
        """
        # Look up Search client class to see if exists or create
        search_client = self._search_index_client.get_search_client(collection_name.lower())
        docs_to_delete = {SEARCH_FIELD_ID: encode_id(key)}

        await search_client.delete_documents(documents=[docs_to_delete])
        await search_client.close()

    async def get_nearest_match(
        self,
        collection_name: str,
        embedding: ndarray,
        min_relevance_score: float = 0.0,
        with_embedding: bool = False,
    ) -> tuple[MemoryRecord, float]:
        """Gets the nearest match to an embedding using vector configuration parameters.

        Args:
            collection_name (str): The name of the collection to get the nearest match from.
            embedding (ndarray): The embedding to find the nearest match to.
            min_relevance_score (float): The minimum relevance score of the match. (default: {0.0})
            with_embedding (bool): Whether to include the embedding in the result. (default: {False})

        Returns:
            Tuple[MemoryRecord, float]: The record and the relevance score.
        """
        memory_records = await self.get_nearest_matches(
            collection_name=collection_name,
            embedding=embedding,
            min_relevance_score=min_relevance_score,
            with_embeddings=with_embedding,
            limit=1,
        )

        if len(memory_records) > 0:
            return memory_records[0]
        return None

    async def get_nearest_matches(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float = 0.0,
        with_embeddings: bool = False,
    ) -> list[tuple[MemoryRecord, float]]:
        """Gets the nearest matches to an embedding using vector configuration.

        Parameters:
            collection_name (str)      : The name of the collection to get the nearest matches from.
            embedding (ndarray)        : The embedding to find the nearest matches to.
            limit (int): The maximum number of matches to return.
            min_relevance_score (float): The minimum relevance score of the matches. (default: {0.0})
            with_embeddings (bool): Whether to include the embeddings in the results. (default: {False})

        Returns:
            List[Tuple[MemoryRecord, float]]: The records and their relevance scores.
        """
        # Look up Search client class to see if exists or create
        search_client = self._search_index_client.get_search_client(collection_name.lower())

        vector = VectorizedQuery(vector=embedding.flatten(), k_nearest_neighbors=limit, fields=SEARCH_FIELD_EMBEDDING)

        search_results = await search_client.search(
            search_text="*",
            select=get_field_selection(with_embeddings),
            vector_queries=[vector],
        )

        if not search_results or search_results is None:
            await search_client.close()
            return []

        # Convert the results to MemoryRecords
        nearest_results = []
        async for search_record in search_results:
            if search_record["@search.score"] < min_relevance_score:
                continue

            memory_record = dict_to_memory_record(search_record, with_embeddings)
            nearest_results.append((memory_record, search_record["@search.score"]))

        await search_client.close()
        return nearest_results
