# Copyright (c) Microsoft. All rights reserved.

import uuid
from logging import Logger
from typing import List, Optional, Tuple

from azure.core.credentials import AzureKeyCredential, TokenCredential
from azure.core.exceptions import ResourceNotFoundError
from azure.search.documents.indexes.aio import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswVectorSearchAlgorithmConfiguration,
    SearchIndex,
    VectorSearch,
)
from azure.search.documents.models import Vector
from numpy import ndarray

from azure.search.documents.indexes.models import (
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SimpleField,
)
from semantic_kernel.connectors.memory.azure_cognitive_search.utils import (
    decode_id,
    encode_id,
    get_search_index_async_client,
    SEARCH_FIELD_ID_KEY,
    SEARCH_FIELD_TEXT_KEY,
    SEARCH_FIELD_EMBEDDING_KEY,
    SEARCH_FIELD_SRC_KEY,
    SEARCH_FIELD_DESC_KEY,
    SEARCH_FIELD_METADATA_KEY,
    SEARCH_FIELD_IS_REF_KEY,
)
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.null_logger import NullLogger

class AzureCognitiveSearchMemoryStore(MemoryStoreBase):
    _search_index_client: SearchIndexClient = None
    _vector_size: int = None
    _logger: Logger = None

    def __init__(
        self,
        vector_size: int,
        search_endpoint: Optional[str] = None,
        admin_key: Optional[str] = None,
        azure_credentials: Optional[AzureKeyCredential] = None,
        token_credentials: Optional[TokenCredential] = None,
        custom_schema: Optional[dict] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        """Initializes a new instance of the AzureCognitiveSearchMemoryStore class.

        Arguments:
            vector_size {int}                                -- Embedding vector size.
            search_endpoint {Optional[str]}                  -- The endpoint of the Azure Cognitive Search service
                                                                (default: {None}).
            admin_key {Optional[str]}                        -- Azure Cognitive Search API key (default: {None}).
            azure_credentials {Optional[AzureKeyCredential]} -- Azure Cognitive Search credentials (default: {None}).
            token_credentials {Optional[TokenCredential]}    -- Azure Cognitive Search token credentials
                                                                (default: {None}).
            logger {Optional[Logger]}                        -- The logger to use (default: {None}).

        Instantiate using Async Context Manager:
            async with AzureCognitiveSearchMemoryStore(<...>) as memory:
                await memory.<...>
        """
        try:
            pass
        except ImportError:
            raise ValueError(
                "Error: Unable to import Azure Cognitive Search client python package."
                "Please install Azure Cognitive Search client"
            )
        self._schema = {
            SEARCH_FIELD_ID_KEY : custom_schema.get("SEARCH_FIELD_ID", "Id"),
            SEARCH_FIELD_TEXT_KEY : custom_schema.get("SEARCH_FIELD_TEXT", "Text"),
            SEARCH_FIELD_EMBEDDING_KEY : custom_schema.get("SEARCH_FIELD_EMBEDDING", "Embedding"),
            SEARCH_FIELD_SRC_KEY : custom_schema.get("SEARCH_FIELD_SRC", "ExternalSourceName"),
            SEARCH_FIELD_DESC_KEY : custom_schema.get("SEARCH_FIELD_DESC", "Description"),
            SEARCH_FIELD_METADATA_KEY : custom_schema.get("SEARCH_FIELD_METADATA", "AdditionalMetadata"),
            SEARCH_FIELD_IS_REF_KEY : custom_schema.get("SEARCH_FIELD_IS_REF", "IsReference"),
        }
        self._logger = logger or NullLogger()
        self._vector_size = vector_size
        self._search_index_client = get_search_index_async_client(
            search_endpoint, admin_key, azure_credentials, token_credentials
        )

    async def close_async(self):
        """Async close connection, invoked by MemoryStoreBase.__aexit__()"""
        if self._search_index_client is not None:
            await self._search_index_client.close()

    async def create_collection_async(
        self,
        collection_name: str,
        vector_config: Optional[HnswVectorSearchAlgorithmConfiguration] = None,
    ) -> None:
        """Creates a new collection if it does not exist.

        Arguments:
            collection_name {str}                              -- The name of the collection to create.
            vector_config {HnswVectorSearchAlgorithmConfiguration} -- Optional search algorithm configuration
                                                                      (default: {None}).
            semantic_config {SemanticConfiguration}            -- Optional search index configuration (default: {None}).
        Returns:
            None
        """

        if vector_config:
            vector_search = VectorSearch(algorithm_configurations=[vector_config])
        else:
            vector_search = VectorSearch(
                algorithm_configurations=[
                    HnswVectorSearchAlgorithmConfiguration(
                        name="az-vector-config",
                        kind="hnsw",
                        hnsw_parameters={
                            # Number of bi-directional links, 4 to 10
                            "m": 4,
                            # Size of nearest neighbors list during indexing, 100 to 1000
                            "efConstruction": 400,
                            # Size of nearest neighbors list during search, 100 to 1000
                            "efSearch": 500,
                            # cosine, dotProduct, euclidean
                            "metric": "cosine",
                        },
                    )
                ]
            )

        if not self._search_index_client:
            raise ValueError("Error: self._search_index_client not set 1.")

        if self._search_index_client is None:
            raise ValueError("Error: self._search_index_client not set 2.")

        # Check to see if collection exists
        collection_index = None
        try:
            collection_index = await self._search_index_client.get_index(
                collection_name.lower()
            )
        except ResourceNotFoundError:
            pass

        if not collection_index:
            # Create the search index with the semantic settings
            index = SearchIndex(
                name=collection_name.lower(),
                fields=self.get_index_schema(self._vector_size),
                vector_search=vector_search,
            )

            await self._search_index_client.create_index(index)

    async def get_collections_async(self) -> List[str]:
        """Gets the list of collections.

        Returns:
            List[str] -- The list of collections.
        """

        results_list = []
        try:
            items = await self._search_index_client.list_index_names()
        except TypeError:
            # Note: used on Windows
            items = self._search_index_client.list_index_names()

        async for result in items:
            results_list.append(result)

        return results_list

    async def delete_collection_async(self, collection_name: str) -> None:
        """Deletes a collection.

        Arguments:
            collection_name {str} -- The name of the collection to delete.

        Returns:
            None
        """
        await self._search_index_client.delete_index(index=collection_name.lower())

    async def does_collection_exist_async(self, collection_name: str) -> bool:
        """Checks if a collection exists.

        Arguments:
            collection_name {str} -- The name of the collection to check.

        Returns:
            bool -- True if the collection exists; otherwise, False.
        """

        try:
            collection_result = await self._search_index_client.get_index(
                name=collection_name.lower()
            )

            if collection_result:
                return True
            else:
                return False
        except ResourceNotFoundError:
            return False

    async def upsert_async(self, collection_name: str, record: MemoryRecord) -> str:
        """Upsert a record.

        Arguments:
            collection_name {str} -- The name of the collection to upsert the record into.
            record {MemoryRecord} -- The record to upsert.

        Returns:
            str -- The unique record id of the record.
        """

        result = await self.upsert_batch_async(collection_name, [record])
        if result:
            return result[0]
        return None

    async def upsert_batch_async(
        self, collection_name: str, records: List[MemoryRecord]
    ) -> List[str]:
        """Upsert a batch of records.

        Arguments:
            collection_name {str}        -- The name of the collection to upsert the records into.
            records {List[MemoryRecord]} -- The records to upsert.

        Returns:
            List[str] -- The unique database keys of the records.
        """

        # Initialize search client here
        # Look up Search client class to see if exists or create
        search_client = self._search_index_client.get_search_client(
            collection_name.lower()
        )

        search_records = []
        search_ids = []

        for record in records:
            # Note:
            # * Document id     = user provided value
            # * MemoryRecord.id = base64(Document id)
            if not record._id:
                record._id = str(uuid.uuid4())

            search_record = self.memory_record_to_search_record(record)
            search_records.append(search_record)
            search_ids.append(record._id)

        result = await search_client.upload_documents(documents=search_records)
        await search_client.close()

        if result[0].succeeded:
            return search_ids
        else:
            return None

    async def get_async(
        self, collection_name: str, key: str, with_embedding: bool = False
    ) -> MemoryRecord:
        """Gets a record.

        Arguments:
            collection_name {str} -- The name of the collection to get the record from.
            key {str}             -- The unique database key of the record.
            with_embedding {bool} -- Whether to include the embedding in the result. (default: {False})

        Returns:
            MemoryRecord -- The record.
        """

        # Look up Search client class to see if exists or create
        search_client = self._search_index_client.get_search_client(
            collection_name.lower()
        )

        try:
            search_result = await search_client.get_document(
                key=encode_id(key), selected_fields=self.get_field_selection(with_embedding)
            )
        except ResourceNotFoundError:
            await search_client.close()
            raise KeyError("Memory record not found")

        await search_client.close()

        # Create Memory record from document
        return self.dict_to_memory_record(search_result, with_embedding)

    async def get_batch_async(
        self, collection_name: str, keys: List[str], with_embeddings: bool = False
    ) -> List[MemoryRecord]:
        """Gets a batch of records.

        Arguments:
            collection_name {str}  -- The name of the collection to get the records from.
            keys {List[str]}       -- The unique database keys of the records.
            with_embeddings {bool} -- Whether to include the embeddings in the results. (default: {False})

        Returns:
            List[MemoryRecord] -- The records.
        """

        search_results = []

        for key in keys:
            search_result = await self.get_async(
                collection_name=collection_name.lower(),
                key=key,
                with_embedding=with_embeddings,
            )
            search_results.append(search_result)

        return search_results

    async def remove_batch_async(self, collection_name: str, keys: List[str]) -> None:
        """Removes a batch of records.

        Arguments:
            collection_name {str} -- The name of the collection to remove the records from.
            keys {List[str]}      -- The unique database keys of the records to remove.

        Returns:
            None
        """

        for record_id in keys:
            await self.remove_async(
                collection_name=collection_name.lower(), key=encode_id(record_id)
            )

    async def remove_async(self, collection_name: str, key: str) -> None:
        """Removes a record.

        Arguments:
            collection_name {str} -- The name of the collection to remove the record from.
            key {str}             -- The unique database key of the record to remove.

        Returns:
            None
        """

        # Look up Search client class to see if exists or create
        search_client = self._search_index_client.get_search_client(
            collection_name.lower()
        )
        docs_to_delete = {self._schema[SEARCH_FIELD_ID_KEY]: encode_id(key)}

        await search_client.delete_documents(documents=[docs_to_delete])
        await search_client.close()

    async def get_nearest_match_async(
        self,
        collection_name: str,
        embedding: ndarray,
        min_relevance_score: float = 0.0,
        with_embedding: bool = False,
    ) -> Tuple[MemoryRecord, float]:
        """Gets the nearest match to an embedding using vector configuration parameters.

        Arguments:
            collection_name {str}       -- The name of the collection to get the nearest match from.
            embedding {ndarray}         -- The embedding to find the nearest match to.
            min_relevance_score {float} -- The minimum relevance score of the match. (default: {0.0})
            with_embedding {bool}       -- Whether to include the embedding in the result. (default: {False})

        Returns:
            Tuple[MemoryRecord, float] -- The record and the relevance score.
        """

        memory_records = await self.get_nearest_matches_async(
            collection_name=collection_name,
            embedding=embedding,
            min_relevance_score=min_relevance_score,
            with_embeddings=with_embedding,
            limit=1,
        )

        if len(memory_records) > 0:
            return memory_records[0]
        else:
            return None

    async def get_nearest_matches_async(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float = 0.0,
        with_embeddings: bool = False,
    ) -> List[Tuple[MemoryRecord, float]]:
        """Gets the nearest matches to an embedding using vector configuration.

        Parameters:
            collection_name (str)       -- The name of the collection to get the nearest matches from.
            embedding (ndarray)         -- The embedding to find the nearest matches to.
            limit {int}                 -- The maximum number of matches to return.
            min_relevance_score {float} -- The minimum relevance score of the matches. (default: {0.0})
            with_embeddings {bool}      -- Whether to include the embeddings in the results. (default: {False})

        Returns:
            List[Tuple[MemoryRecord, float]] -- The records and their relevance scores.
        """

        # Look up Search client class to see if exists or create
        search_client = self._search_index_client.get_search_client(
            collection_name.lower()
        )

        vector = Vector(
            value=embedding.flatten(), k=limit, fields=self._schema[SEARCH_FIELD_EMBEDDING_KEY]
        )

        search_results = await search_client.search(
            search_text="*",
            vectors=[vector],
            select=self.get_field_selection(with_embeddings),
        )

        if not search_results or search_results is None:
            await search_client.close()
            return []

        # Convert the results to MemoryRecords
        nearest_results = []
        async for search_record in search_results:
            if search_record["@search.score"] < min_relevance_score:
                continue

            memory_record = self.dict_to_memory_record(search_record, with_embeddings)
            nearest_results.append((memory_record, search_record["@search.score"]))

        await search_client.close()
        return nearest_results
    

    def get_index_schema(self, vector_size: int) -> list:
        """Return the schema of search indexes.

        Arguments:
            vector_size {int} -- The size of the vectors being stored in collection/index.

        Returns:
            list -- The Azure Cognitive Search schema as list type.
        """

        search_fields = [
            SimpleField(
                name=self._schema[SEARCH_FIELD_ID_KEY],
                type=SearchFieldDataType.String,
                searchable=True,
                filterable=True,
                retrievable=True,
                key=True,
            ),
            SearchableField(
                name=self._schema[SEARCH_FIELD_TEXT_KEY],
                type=SearchFieldDataType.String,
                searchable=True,
                filterable=True,
                retrievable=True,
            ),
            SearchField(
                name=self._schema[SEARCH_FIELD_EMBEDDING_KEY],
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=vector_size,
                vector_search_configuration="az-vector-config",
            ),
            SimpleField(
                name=self._schema[SEARCH_FIELD_SRC_KEY],
                type=SearchFieldDataType.String,
                searchable=True,
                filterable=True,
                retrievable=True,
            ),
            SimpleField(
                name=self._schema[SEARCH_FIELD_DESC_KEY],
                type=SearchFieldDataType.String,
                searchable=True,
                filterable=True,
                retrievable=True,
            ),
            SimpleField(
                name=self._schema[SEARCH_FIELD_METADATA_KEY],
                type=SearchFieldDataType.String,
                searchable=True,
                filterable=True,
                retrievable=True,
            ),
            SimpleField(
                name=self._schema[SEARCH_FIELD_IS_REF_KEY],
                type=SearchFieldDataType.Boolean,
                searchable=True,
                filterable=True,
                retrievable=True,
            ),
        ]

        return search_fields


    def get_field_selection(self, with_embeddings: bool) -> List[str]:
        """Get the list of fields to search and load.

        Arguments:
            with_embedding {bool} -- Whether to include the embedding vector field.

        Returns:
            List[str] -- List of fields.
        """

        field_selection = [
            self._schema[SEARCH_FIELD_ID_KEY],
            self._schema[SEARCH_FIELD_TEXT_KEY],
            self._schema[SEARCH_FIELD_SRC_KEY],
            self._schema[SEARCH_FIELD_DESC_KEY],
            self._schema[SEARCH_FIELD_METADATA_KEY],
            self._schema[SEARCH_FIELD_IS_REF_KEY],
        ]

        if with_embeddings:
            field_selection.append(self._schema[SEARCH_FIELD_EMBEDDING_KEY])

        return field_selection


    def dict_to_memory_record(self, data: dict, with_embeddings: bool) -> MemoryRecord:
        """Converts a search result to a MemoryRecord.

        Arguments:
            data {dict} -- Azure Cognitive Search result data.

        Returns:
            MemoryRecord -- The MemoryRecord from Azure Cognitive Search Data Result.
        """

        sk_result = MemoryRecord(
            id=decode_id(data[self._schema[SEARCH_FIELD_ID_KEY]]),
            key=data[self._schema[SEARCH_FIELD_ID_KEY]],
            text=data[self._schema[SEARCH_FIELD_TEXT_KEY]],
            external_source_name=data[self._schema[SEARCH_FIELD_SRC_KEY]],
            description=data[self._schema[SEARCH_FIELD_DESC_KEY]],
            additional_metadata=data[self._schema[SEARCH_FIELD_METADATA_KEY]],
            is_reference=data[self._schema[SEARCH_FIELD_IS_REF_KEY]],
            embedding=data[self._schema[SEARCH_FIELD_EMBEDDING_KEY]] if with_embeddings else None,
            timestamp=None,
        )
        return sk_result


    def memory_record_to_search_record(self, record: MemoryRecord) -> dict:
        """Convert a MemoryRecord to a dictionary

        Arguments:
            record {MemoryRecord} -- The MemoryRecord from Azure Cognitive Search Data Result.

        Returns:
            data {dict} -- Dictionary data.
        """

        return {
                self._schema[SEARCH_FIELD_ID_KEY]: encode_id(record._id),
            self._schema[SEARCH_FIELD_TEXT_KEY]: str(record._text),
            self._schema[SEARCH_FIELD_SRC_KEY]: record._external_source_name or "",
            self._schema[SEARCH_FIELD_DESC_KEY]: record._description or "",
            self._schema[SEARCH_FIELD_METADATA_KEY]: record._additional_metadata or "",
            self._schema[SEARCH_FIELD_IS_REF_KEY]: str(record._is_reference),
            self._schema[SEARCH_FIELD_EMBEDDING_KEY]: record._embedding.tolist(),
        }