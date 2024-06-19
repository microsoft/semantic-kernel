# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import sys
from typing import Any, TypeVar

from azure.core.credentials import AzureKeyCredential, TokenCredential
from azure.core.exceptions import ResourceNotFoundError
from azure.search.documents.indexes.aio import SearchIndexClient
from pydantic import ValidationError

from semantic_kernel.kernel import Kernel

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

from semantic_kernel.connectors.data.azure_ai_search.utils import get_search_index_async_client
from semantic_kernel.data.vector_record_store_base import VectorRecordStoreBase
from semantic_kernel.exceptions import MemoryConnectorInitializationError, MemoryConnectorResourceNotFound
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)

DataModelT = TypeVar("DataModelT")


@experimental_class
class AzureAISearchVectorRecordStore(VectorRecordStoreBase[DataModelT, str]):
    _search_index_client: SearchIndexClient | None = None

    def __init__(
        self,
        item_type: type[DataModelT],
        collection_name: str | None = None,
        kernel: Kernel | None = None,
        search_endpoint: str | None = None,
        api_key: str | None = None,
        azure_credentials: AzureKeyCredential | None = None,
        token_credentials: TokenCredential | None = None,
        search_index_client: SearchIndexClient | None = None,
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
            api_key (str | None): Azure Cognitive Search API key (default: {None}).
            azure_credentials (AzureKeyCredential | None): Azure Cognitive Search credentials (default: {None}).
            token_credentials (TokenCredential | None): Azure Cognitive Search token credentials
                (default: {None}).
            search_index_client (SearchIndexClient | None): The search index client (default: {None}).
            env_file_path (str | None): Use the environment settings file as a fallback
                to environment variables
            env_file_encoding (str | None): The encoding of the environment settings file
            kernel (Kernel | None): The kernel instance, used if embeddings need to be created.

        """
        from semantic_kernel.connectors.data.azure_ai_search.azure_ai_search_settings import (
            AzureAISearchSettings,
        )

        try:
            azure_ai_search_settings = AzureAISearchSettings.create(
                env_file_path=env_file_path,
                endpoint=search_endpoint,
                api_key=api_key,
                env_file_encoding=env_file_encoding,
                index_name=collection_name,
            )
        except ValidationError as exc:
            raise MemoryConnectorInitializationError("Failed to create Azure Cognitive Search settings.") from exc

        super().__init__(item_type=item_type, collection_name=azure_ai_search_settings.index_name, kernel=kernel)
        self._search_index_client = search_index_client or get_search_index_async_client(
            azure_ai_search_settings=azure_ai_search_settings,
            azure_credential=azure_credentials,
            token_credential=token_credentials,
        )

    async def close(self):
        """Async close connection, invoked by MemoryStoreBase.__aexit__()."""
        if self._search_index_client is not None:
            await self._search_index_client.close()

    @override
    async def upsert(
        self,
        record: object,
        collection_name: str | None = None,
        generate_embeddings: bool = True,
        **kwargs: Any,
    ) -> str | None:
        result = await self.upsert_batch([record], collection_name, generate_embeddings, **kwargs)

        return result[0] if result else None

    @override
    async def upsert_batch(
        self,
        records: list[object],
        collection_name: str | None = None,
        generate_embeddings: bool = True,
        **kwargs,
    ) -> list[str] | None:
        if not self._search_index_client:
            raise MemoryConnectorInitializationError("Azure AI Search client is not initialized.")
        if generate_embeddings and self._kernel:
            records = await self._kernel.add_vector_to_records(records, **kwargs)

        docs: list[dict[str, Any]] = [self._serialize_data_model_to_store_model(record) for record in records]
        async with self._search_index_client.get_search_client(
            self._get_collection_name(collection_name)
        ) as search_client:
            result = await search_client.merge_or_upload_documents(documents=docs)

            if result[0].succeeded:
                return [res.key for res in result]
            return None

    @override
    async def get(self, key: str, collection_name: str | None = None, **kwargs) -> object:
        if not self._search_index_client:
            raise MemoryConnectorInitializationError("Azure AI Search client is not initialized.")
        async with self._search_index_client.get_search_client(
            self._get_collection_name(collection_name)
        ) as search_client:
            try:
                search_result = await search_client.get_document(
                    key=key, selected_fields=kwargs.get("selected_fields", None)
                )
                return self._deserialize_store_model_to_data_model(search_result)
            except ResourceNotFoundError as exc:
                raise MemoryConnectorResourceNotFound("Memory record not found") from exc

    @override
    async def get_batch(self, keys: list[str], collection_name: str | None = None, **kwargs: Any) -> list[object]:
        return await asyncio.gather(*[self.get(key=key, collection_name=collection_name, **kwargs) for key in keys])

    @override
    async def delete(self, key: str, collection_name: str | None = None, **kwargs: Any) -> None:
        await self.delete_batch([key], collection_name, **kwargs)

    @override
    async def delete_batch(self, keys: list[str], collection_name: str | None = None, **kwargs: Any) -> None:
        docs_to_delete = [{self._key_field: key} for key in keys]
        async with self._search_index_client.get_search_client(
            self._get_collection_name(collection_name)
        ) as search_client:
            await search_client.delete_documents(documents=docs_to_delete)

    @override
    @property
    def supported_key_types(self) -> list[type] | None:
        return [str]
