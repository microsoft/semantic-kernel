# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import sys
from typing import Any, TypeVar

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

from azure.search.documents.aio import SearchClient

from semantic_kernel.data.models.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_record_store_base import VectorRecordStoreBase
from semantic_kernel.kernel import Kernel
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)

TModel = TypeVar("TModel")


@experimental_class
class AzureAISearchVectorRecordStore(VectorRecordStoreBase[str, TModel]):
    def __init__(
        self,
        search_client: SearchClient,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        kernel: Kernel | None = None,
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
        super().__init__(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=search_client._index_name,
            kernel=kernel,
        )
        self._search_client = search_client

    async def close(self):
        """Async close connection, invoked by MemoryStoreBase.__aexit__()."""
        await self._search_client.close()

    @override
    async def _inner_upsert(
        self,
        records: list[Any],
        collection_name: str | None = None,
        **kwargs: Any,
    ) -> list[str]:
        results = await self._search_client.merge_or_upload_documents(documents=records, **kwargs)
        return [result.key for result in results]  # type: ignore

    @override
    async def _inner_get(
        self, keys: list[str], collection_name: str | None = None, **kwargs: Any
    ) -> list[dict[str, Any]]:
        client = self._search_client
        return await asyncio.gather(
            *[client.get_document(key=key, selected_fields=kwargs.get("selected_fields", ["*"])) for key in keys]
        )

    @override
    async def _inner_delete(self, keys: list[str], collection_name: str | None = None, **kwargs: Any) -> None:
        await self._search_client.delete_documents(documents=[{self._key_field: key} for key in keys])

    @override
    @property
    def supported_key_types(self) -> list[type] | None:
        return [str]

    @override
    @property
    def supported_vector_types(self) -> list[type] | None:
        return [list[float], list[int]]

    @override
    def _serialize_dicts_to_store_models(self, records: list[dict[str, Any]], **kwargs: Any) -> list[Any]:
        """Serialize a dict of the data to the store model.

        This method should be overridden by the child class to convert the dict to the store model.
        """
        return records

    @override
    def _deserialize_store_models_to_dicts(self, records: list[Any], **kwargs: Any) -> list[dict[str, Any]]:
        """Deserialize the store model to a dict.

        This method should be overridden by the child class to convert the store model to a dict.
        """
        return records
