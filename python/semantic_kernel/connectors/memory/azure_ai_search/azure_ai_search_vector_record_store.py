# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from typing import Any, TypeVar, overload

from azure.core.credentials import AzureKeyCredential, TokenCredential
from azure.core.exceptions import ResourceNotFoundError
from azure.search.documents.indexes.aio import SearchIndexClient
from pydantic import ValidationError

from semantic_kernel.connectors.memory.azure_ai_search.utils import get_search_index_async_client
from semantic_kernel.exceptions import MemoryConnectorInitializationError, MemoryConnectorResourceNotFound
from semantic_kernel.memory.protocols.vector_record_store_base import VectorRecordStoreBase
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)

DataModelT = TypeVar("DataModelT")


@experimental_class
class AzureAISearchVectorRecordStore(VectorRecordStoreBase[DataModelT, str]):
    _search_index_client: SearchIndexClient = None
    _vector_size: int = None

    def __init__(
        self,
        item_type: type[DataModelT],
        collection_name: str | None = None,
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
            item_type (type[DataModelT]): The type of the data model.
            collection_name (str): The name of the collection, optional.
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
        from semantic_kernel.connectors.memory.azure_ai_search.azure_ai_search_settings import (
            AzureAISearchSettings,
        )

        try:
            azure_ai_search_settings = AzureAISearchSettings.create(
                env_file_path=env_file_path,
                endpoint=search_endpoint,
                api_key=admin_key,
                env_file_encoding=env_file_encoding,
                index_name=collection_name,
            )
        except ValidationError as exc:
            raise MemoryConnectorInitializationError("Failed to create Azure Cognitive Search settings.") from exc

        super().__init__(item_type=item_type, key_type=str, collection_name=azure_ai_search_settings.index_name)
        self._search_index_client = get_search_index_async_client(
            azure_ai_search_settings=azure_ai_search_settings,
            azure_credential=azure_credentials,
            token_credential=token_credentials,
        )

    async def close(self):
        """Async close connection, invoked by MemoryStoreBase.__aexit__()."""
        if self._search_index_client is not None:
            await self._search_index_client.close()

    # # region: MemoryCollectionCreateProtocol

    # async def create_collection(
    #     self,
    #     collection_name: str | None = None,
    #     vector_config: HnswAlgorithmConfiguration | None = None,
    #     search_resource_encryption_key: SearchResourceEncryptionKey | None = None,
    #     **kwargs: Any,
    # ) -> None:
    #     """Creates a new collection if it does not exist.

    #     Args:
    #         collection_name (str): The name of the collection to create.
    #         vector_config (HnswVectorSearchAlgorithmConfiguration):
    #             Optional search algorithm configuration (default: {None}).
    #         search_resource_encryption_key (SearchResourceEncryptionKey):
    #             Optional Search Encryption Key (default: {None}).
    #         kwargs: Additional keyword arguments.

    #     Returns:
    #         None
    #     """
    #     collection_name = self._get_collection_name(collection_name).lower()
    #     vector_search_profile_name = "az-vector-config"
    #     if vector_config:
    #         vector_search_profile = VectorSearchProfile(
    #             name=vector_search_profile_name, algorithm_configuration_name=vector_config.name
    #         )
    #         vector_search = VectorSearch(profiles=[vector_search_profile], algorithms=[vector_config])
    #     else:
    #         vector_search_algorithm_name = "az-vector-hnsw-config"
    #         vector_search_profile = VectorSearchProfile(
    #             name=vector_search_profile_name, algorithm_configuration_name=vector_search_algorithm_name
    #         )
    #         vector_search = VectorSearch(
    #             profiles=[vector_search_profile],
    #             algorithms=[
    #                 HnswAlgorithmConfiguration(
    #                     name=vector_search_algorithm_name,
    #                     kind="hnsw",
    #                     parameters=HnswParameters(
    #                         m=4,  # Number of bidirectional links, typically between 4 and 10
    #                         ef_construction=400,  # Size during indexing, range: 100-1000
    #                         ef_search=500,  # Size during search, range: 100-1000
    #                         metric="cosine",  # Can be "cosine", "dotProduct", or "euclidean"
    #                     ),
    #                 )
    #             ],
    #         )

    #     if not self._search_index_client:
    #         raise MemoryConnectorInitializationError("Error: self._search_index_client not set 1.")

    #     # Check to see if collection exists
    #     collection_index = None
    #     with contextlib.suppress(ResourceNotFoundError):
    #         collection_index = await self._search_index_client.get_index(collection_name)

    #     if not collection_index:
    #         # Create the search index with the semantic settings
    #         index = SearchIndex(
    #             name=collection_name,
    #             fields=get_index_schema(self._vector_size, vector_search_profile_name),
    #             vector_search=vector_search,
    #             encryption_key=search_resource_encryption_key,
    #         )

    #         await self._search_index_client.create_index(index)

    # # endregion
    # # region: MemoryCollectionUpdateProtocol

    # async def get_collection_names(self, **kwargs) -> list[str]:
    #     """Gets the list of collections.

    #     Args:
    #         kwargs: Additional keyword arguments.

    #     Returns:
    #         List[str]: The list of collections.
    #     """
    #     results_list = []
    #     items = self._search_index_client.list_index_names()
    #     if isawaitable(items):
    #         items = await items

    #     async for result in items:
    #         results_list.append(result)

    #     return results_list

    # async def delete_collection(self, collection_name: str | None = None, **kwargs) -> None:
    #     """Deletes a collection.

    #     Args:
    #         collection_name (str): The name of the collection to delete.
    #         kwargs: Additional keyword arguments.

    #     Returns:
    #         None
    #     """
    #     await self._search_index_client.delete_index(index=self._get_collection_name(collection_name).lower())

    # async def collection_exists(self, collection_name: str | None = None, **kwargs) -> bool:
    #     """Checks if a collection exists.

    #     Args:
    #         collection_name (str): The name of the collection to check.
    #         kwargs: Additional keyword arguments.

    #     Returns:
    #         bool: True if the collection exists; otherwise, False.
    #     """
    #     try:
    #         collection_result = await self._search_index_client.get_index(
    #             name=self._get_collection_name(collection_name).lower()
    #         )

    #         return bool(collection_result)
    #     except ResourceNotFoundError:
    #         return False

    # # endregion

    @overload
    async def upsert(self, record: DataModelT, collection_name: str | None = None, **kwargs: Any) -> str:
        result = await self.upsert_batch([record], collection_name, **kwargs)

        return result[0] if result else None

    @overload
    async def upsert_batch(
        self, records: list[DataModelT], collection_name: str | None = None, **kwargs
    ) -> list[str] | None:
        # Initialize search client here
        # Look up Search client class to see if exists or create
        search_client = self._search_index_client.get_search_client(self._get_collection_name(collection_name))

        docs: dict[str, dict[str, Any]] = {
            getattr(record, self._key_field): self._serialize_data_model_to_store_model(record) for record in records
        }

        result = await search_client.merge_or_upload_documents(documents=list(docs.values()))
        await search_client.close()

        if result[0].succeeded:
            return list(docs.keys())
        return None

    @overload
    async def get(self, key: str, collection_name: str | None = None, **kwargs) -> DataModelT:
        search_client = self._search_index_client.get_search_client(self._get_collection_name(collection_name))

        try:
            search_result = await search_client.get_document(
                key=key, selected_fields=kwargs["selected_fields"] if "selected_fields" in kwargs else None
            )
            return self._deserialize_store_model_to_data_model(search_result)
        except ResourceNotFoundError as exc:
            raise MemoryConnectorResourceNotFound("Memory record not found") from exc
        finally:
            await search_client.close()

    @overload
    async def get_batch(self, keys: list[str], collection_name: str | None = None, **kwargs: Any) -> list[DataModelT]:
        return await asyncio.gather(*[self.get(key=key, collection_name=collection_name, **kwargs) for key in keys])

    @overload
    async def delete(self, key: str, collection_name: str | None = None, **kwargs: Any) -> None:
        await self.delete_batch([key], collection_name, **kwargs)

    @overload
    async def delete_batch(self, keys: list[str], collection_name: str | None = None, **kwargs: Any) -> None:
        search_client = self._search_index_client.get_search_client(self._get_collection_name(collection_name))
        docs_to_delete = [{self._key_field: key} for key in keys]

        await search_client.delete_documents(documents=docs_to_delete)
        await search_client.close()

    def _get_collection_name(self, collection_name: str | None = None):
        return super()._get_collection_name(collection_name).lower()
