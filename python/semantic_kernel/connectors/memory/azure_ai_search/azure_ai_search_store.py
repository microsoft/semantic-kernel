# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from typing import TYPE_CHECKING, Any, TypeVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from azure.core.credentials import AzureKeyCredential, TokenCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.indexes.aio import SearchIndexClient
from pydantic import ValidationError

from semantic_kernel.connectors.memory.azure_ai_search.azure_ai_search_collection import (
    AzureAISearchCollection,
)
from semantic_kernel.connectors.memory.azure_ai_search.utils import get_search_client, get_search_index_client
from semantic_kernel.data.models.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_store import VectorStore
from semantic_kernel.exceptions import MemoryConnectorInitializationError
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.data.vector_store_record_collection import VectorStoreRecordCollection


logger: logging.Logger = logging.getLogger(__name__)

TModel = TypeVar("TModel")


@experimental_class
class AzureAISearchStore(VectorStore):
    search_index_client: SearchIndexClient

    def __init__(
        self,
        search_endpoint: str | None = None,
        api_key: str | None = None,
        azure_credentials: AzureKeyCredential | None = None,
        token_credentials: TokenCredential | None = None,
        search_index_client: SearchIndexClient | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initializes a new instance of the AzureAISearchStore client.

        Instantiate using Async Context Manager:
            async with AzureAISearchStore(<...>) as memory:
                await memory.<...>

        Args:
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

        if not search_index_client:
            try:
                azure_ai_search_settings = AzureAISearchSettings.create(
                    env_file_path=env_file_path,
                    endpoint=search_endpoint,
                    api_key=api_key,
                    env_file_encoding=env_file_encoding,
                )
            except ValidationError as exc:
                raise MemoryConnectorInitializationError("Failed to create Azure Cognitive Search settings.") from exc
            search_index_client = get_search_index_client(
                azure_ai_search_settings=azure_ai_search_settings,
                azure_credential=azure_credentials,
                token_credential=token_credentials,
            )

        super().__init__(search_index_client=search_index_client)

    @override
    def get_collection(
        self,
        collection_name: str,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        search_client: SearchClient | None = None,
        **kwargs: Any,
    ) -> "VectorStoreRecordCollection":
        """Get a AzureAISearchCollection tied to a collection.

        Args:
            collection_name (str): The name of the collection.
            data_model_type (type[TModel]): The type of the data model.
            data_model_definition (VectorStoreRecordDefinition | None): The model fields, optional.
            search_client (SearchClient | None): The search client for interacting with Azure AI Search,
                will be created if not supplied.
            **kwargs: Additional keyword arguments, passed to the collection constructor.
        """
        if collection_name not in self.vector_record_collections:
            self.vector_record_collections[collection_name] = AzureAISearchCollection(
                data_model_type=data_model_type,
                data_model_definition=data_model_definition,
                search_index_client=self.search_index_client,
                search_client=search_client or get_search_client(self.search_index_client, collection_name),
                collection_name=collection_name,
                **kwargs,
            )
        return self.vector_record_collections[collection_name]

    @override
    async def list_collection_names(self, **kwargs: Any) -> list[str]:
        if "params" not in kwargs:
            kwargs["params"] = {"select": ["name"]}
        return [index async for index in self.search_index_client.list_index_names(**kwargs)]

    @override
    async def close(self) -> None:
        await self.search_index_client.close()
        for collection in self.vector_record_collections.values():
            await collection.close()
