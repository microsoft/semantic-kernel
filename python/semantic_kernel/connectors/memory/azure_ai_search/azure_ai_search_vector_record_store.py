# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import sys
from typing import Any, TypeVar

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

from azure.core.credentials import AzureKeyCredential, TokenCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.indexes.aio import SearchIndexClient
from pydantic import ValidationError

from semantic_kernel.connectors.memory.azure_ai_search.utils import get_search_index_async_client
from semantic_kernel.data.models.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_record_store_base import VectorRecordStoreBase
from semantic_kernel.exceptions import MemoryConnectorInitializationError
from semantic_kernel.kernel import Kernel
from semantic_kernel.kernel_types import OneOrMany
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)

TModel = TypeVar("TModel")


@experimental_class
class AzureAISearchVectorRecordStore(VectorRecordStoreBase[str, TModel]):
    def __init__(
        self,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
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
            data_model_type (type[TModel]): The type of the data model.
            data_model_definition (VectorStoreRecordDefinition | None): The model fields, optional.
            collection_name (str): The name of the collection, optional.
            kernel: Kernel to use for embedding generation.
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

        """
        from semantic_kernel.connectors.memory.azure_ai_search.azure_ai_search_settings import (
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

        super().__init__(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=azure_ai_search_settings.index_name,
            kernel=kernel,
        )
        self._search_index_client = search_index_client or get_search_index_async_client(
            azure_ai_search_settings=azure_ai_search_settings,
            azure_credential=azure_credentials,
            token_credential=token_credentials,
        )
        if self.collection_name:
            self._search_clients: dict[str, SearchClient] = {
                self.collection_name: self._search_index_client.get_search_client(self.collection_name)
            }
        else:
            self._search_clients = {}

    async def close(self):
        """Async close connection, invoked by MemoryStoreBase.__aexit__()."""
        for search_client in self._search_clients.values():
            await search_client.close()
        await self._search_index_client.close()
        self._search_clients.clear()

    @override
    async def _inner_upsert(
        self,
        records: list[Any],
        collection_name: str | None = None,
        **kwargs: Any,
    ) -> list[str]:
        results = await self._get_search_client(collection_name).merge_or_upload_documents(documents=records, **kwargs)
        return [result.key for result in results]  # type: ignore

    @override
    async def _inner_get(
        self, keys: list[str], collection_name: str | None = None, **kwargs: Any
    ) -> list[dict[str, Any]]:
        client = self._get_search_client(collection_name)
        return await asyncio.gather(
            *[client.get_document(key=key, selected_fields=kwargs.get("selected_fields", None)) for key in keys]
        )

    @override
    async def _inner_delete(self, keys: list[str], collection_name: str | None = None, **kwargs: Any) -> None:
        await self._get_search_client(collection_name).delete_documents(
            documents=[{self._key_field: key} for key in keys]
        )

    @override
    @property
    def supported_key_types(self) -> list[type] | None:
        return [str]

    @override
    def _serialize_dicts_to_store_models(self, record: OneOrMany[dict[str, Any]]) -> OneOrMany[Any]:
        """Serialize a dict of the data to the store model.

        This method should be overridden by the child class to convert the dict to the store model.
        """
        return record

    @override
    def _deserialize_store_models_to_dicts(self, record: OneOrMany[Any]) -> OneOrMany[dict[str, Any]]:
        """Deserialize the store model to a dict.

        This method should be overridden by the child class to convert the store model to a dict.
        """
        return record

    def _get_search_client(self, collection_name: str | None = None) -> SearchClient:
        """Create or get a search client for the specified collection."""
        collection_name = self._get_collection_name(collection_name)
        if collection_name not in self._search_clients:
            self._search_clients[collection_name] = self._search_index_client.get_search_client(collection_name)
        return self._search_clients[collection_name]
