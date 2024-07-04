# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import sys
from typing import Any, TypeVar

from semantic_kernel.exceptions.memory_connector_exceptions import MemoryConnectorInitializationError

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

from azure.search.documents.aio import SearchClient

from semantic_kernel.data.models.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_record_store_base import VectorRecordStoreBase
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)

TModel = TypeVar("TModel")


@experimental_class
class AzureAISearchVectorRecordStore(VectorRecordStoreBase[str, TModel]):
    def __init__(
        self,
        search_client: SearchClient,
        collection_name: str,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        **kwargs: Any,
    ) -> None:
        """Initializes a new instance of the AzureCognitiveSearchMemoryStore class.

        Instantiate using Async Context Manager:
            async with AzureCognitiveSearchMemoryStore(<...>) as memory:
                await memory.<...>

        Args:
            search_client (SearchClient): The search client for interacting with Azure AI Search.
            collection_name (str): The name of the collection, optional.
            data_model_type (type[TModel]): The type of the data model.
            data_model_definition (VectorStoreRecordDefinition | None): The model fields, optional.
            **kwargs: Additional keyword arguments.
                kernel: Kernel to use for embedding generation.

        """
        super().__init__(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=collection_name,
            kernel=kwargs.get("kernel", None),
        )
        self._search_client = search_client
        if self._search_client._index_name != self.collection_name:
            raise MemoryConnectorInitializationError(
                f"Collection name '{collection_name}' does not match the index name '{self._search_client._index_name}'."
            )

    async def close(self):
        """Async close connection, invoked by MemoryStoreBase.__aexit__()."""
        await self._search_client.close()

    @override
    async def _inner_upsert(
        self,
        records: list[Any],
        **kwargs: Any,
    ) -> list[str]:
        results = await self._search_client.merge_or_upload_documents(documents=records, **kwargs)
        return [result.key for result in results]  # type: ignore

    @override
    async def _inner_get(self, keys: list[str], **kwargs: Any) -> list[dict[str, Any]]:
        client = self._search_client
        return await asyncio.gather(
            *[client.get_document(key=key, selected_fields=kwargs.get("selected_fields", ["*"])) for key in keys]
        )

    @override
    async def _inner_delete(self, keys: list[str], **kwargs: Any) -> None:
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
