# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import sys
from collections.abc import Sequence
from typing import Any, ClassVar, Generic, TypeVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from azure.search.documents.aio import SearchClient
from azure.search.documents.indexes.aio import SearchIndexClient
from azure.search.documents.indexes.models import SearchIndex
from pydantic import ValidationError

from semantic_kernel.connectors.memory.azure_ai_search.utils import (
    data_model_definition_to_azure_ai_search_index,
    get_search_client,
    get_search_index_client,
)
from semantic_kernel.data.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_store_record_collection import VectorStoreRecordCollection
from semantic_kernel.data.vector_store_record_fields import VectorStoreRecordVectorField
from semantic_kernel.exceptions import MemoryConnectorException, MemoryConnectorInitializationError
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)

TModel = TypeVar("TModel")


@experimental_class
class AzureAISearchCollection(VectorStoreRecordCollection[str, TModel], Generic[TModel]):
    """Azure AI Search collection implementation."""

    search_client: SearchClient
    search_index_client: SearchIndexClient
    supported_key_types: ClassVar[list[str] | None] = ["str"]
    supported_vector_types: ClassVar[list[str] | None] = ["float", "int"]

    def __init__(
        self,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        collection_name: str | None = None,
        search_index_client: SearchIndexClient | None = None,
        search_client: SearchClient | None = None,
        **kwargs: Any,
    ) -> None:
        """Initializes a new instance of the AzureAISearchCollection class.

        Args:
            data_model_type (type[TModel]): The type of the data model.
            data_model_definition (VectorStoreRecordDefinition): The model definition, optional.
            collection_name (str): The name of the collection, optional.
            search_index_client (SearchIndexClient): The search index client for interacting with Azure AI Search,
                used for creating and deleting indexes.
            search_client (SearchClient): The search client for interacting with Azure AI Search,
                used for record operations.
            **kwargs: Additional keyword arguments, including:
                The same keyword arguments used for AzureAISearchVectorStore:
                    search_endpoint: str | None = None,
                    api_key: str | None = None,
                    azure_credentials: AzureKeyCredential | None = None,
                    token_credentials: AsyncTokenCredential | TokenCredential | None = None,
                    env_file_path: str | None = None,
                    env_file_encoding: str | None = None

        """
        if search_client and search_index_client:
            if not collection_name:
                collection_name = search_client._index_name
            elif search_client._index_name != collection_name:
                raise MemoryConnectorInitializationError(
                    "Search client and search index client have different index names."
                )
            super().__init__(
                data_model_type=data_model_type,
                data_model_definition=data_model_definition,
                collection_name=collection_name,
                search_client=search_client,
                search_index_client=search_index_client,
            )
            return

        if search_index_client:
            if not collection_name:
                raise MemoryConnectorInitializationError("Collection name is required.")
            super().__init__(
                data_model_type=data_model_type,
                data_model_definition=data_model_definition,
                collection_name=collection_name,
                search_client=get_search_client(
                    search_index_client=search_index_client, collection_name=collection_name
                ),
                search_index_client=search_index_client,
            )
            return

        from semantic_kernel.connectors.memory.azure_ai_search.azure_ai_search_settings import (
            AzureAISearchSettings,
        )

        try:
            azure_ai_search_settings = AzureAISearchSettings.create(
                env_file_path=kwargs.get("env_file_path", None),
                endpoint=kwargs.get("search_endpoint", None),
                api_key=kwargs.get("api_key", None),
                env_file_encoding=kwargs.get("env_file_encoding", None),
                index_name=collection_name,
            )
        except ValidationError as exc:
            raise MemoryConnectorInitializationError("Failed to create Azure Cognitive Search settings.") from exc
        search_index_client = get_search_index_client(
            azure_ai_search_settings=azure_ai_search_settings,
            azure_credential=kwargs.get("azure_credentials", None),
            token_credential=kwargs.get("token_credentials", None),
        )
        if not azure_ai_search_settings.index_name:
            raise MemoryConnectorInitializationError("Collection name is required.")

        super().__init__(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=azure_ai_search_settings.index_name,
            search_client=get_search_client(
                search_index_client=search_index_client, collection_name=azure_ai_search_settings.index_name
            ),
            search_index_client=search_index_client,
        )

    @override
    async def _inner_upsert(
        self,
        records: Sequence[Any],
        **kwargs: Any,
    ) -> Sequence[str]:
        if not isinstance(records, list):
            records = list(records)
        results = await self.search_client.merge_or_upload_documents(documents=records, **kwargs)
        return [result.key for result in results]  # type: ignore

    @override
    async def _inner_get(self, keys: Sequence[str], **kwargs: Any) -> Sequence[dict[str, Any]]:
        client = self.search_client
        if "selected_fields" in kwargs:
            selected_fields = kwargs["selected_fields"]
        elif "include_vector" in kwargs and not kwargs["include_vector"]:
            selected_fields = [
                name
                for name, field in self.data_model_definition.fields.items()
                if not isinstance(field, VectorStoreRecordVectorField)
            ]
        else:
            selected_fields = ["*"]

        result = await asyncio.gather(
            *[client.get_document(key=key, selected_fields=selected_fields) for key in keys],
            return_exceptions=True,
        )
        return [res for res in result if not isinstance(res, BaseException)]

    @override
    async def _inner_delete(self, keys: Sequence[str], **kwargs: Any) -> None:
        await self.search_client.delete_documents(documents=[{self._key_field_name: key} for key in keys])

    @override
    def _serialize_dicts_to_store_models(self, records: Sequence[dict[str, Any]], **kwargs: Any) -> Sequence[Any]:
        return records

    @override
    def _deserialize_store_models_to_dicts(self, records: Sequence[Any], **kwargs: Any) -> Sequence[dict[str, Any]]:
        return records

    @override
    async def create_collection(self, **kwargs) -> None:
        """Create a new collection in Azure AI Search.

        Args:
            **kwargs: Additional keyword arguments.
                index (SearchIndex): The search index to create, if this is supplied
                    this is used instead of a index created based on the definition.
                encryption_key (SearchResourceEncryptionKey): The encryption key to use,
                    not used when index is supplied.
                other kwargs are passed to the create_index method.
        """
        if index := kwargs.pop("index", None):
            if isinstance(index, SearchIndex):
                await self.search_index_client.create_index(index=index, **kwargs)
                return
            raise MemoryConnectorException("Invalid index type supplied.")
        await self.search_index_client.create_index(
            index=data_model_definition_to_azure_ai_search_index(
                collection_name=self.collection_name,
                definition=self.data_model_definition,
                encryption_key=kwargs.pop("encryption_key", None),
            ),
            **kwargs,
        )

    @override
    async def does_collection_exist(self, **kwargs) -> bool:
        if "params" not in kwargs:
            kwargs["params"] = {"select": ["name"]}
        return self.collection_name in [
            index_name async for index_name in self.search_index_client.list_index_names(**kwargs)
        ]

    @override
    async def delete_collection(self, **kwargs) -> None:
        await self.search_index_client.delete_index(self.collection_name, **kwargs)
