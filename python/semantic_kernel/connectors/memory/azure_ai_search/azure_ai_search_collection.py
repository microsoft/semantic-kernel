# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import sys
from collections.abc import Sequence
from typing import Any, ClassVar, Generic

from azure.search.documents.aio import SearchClient
from azure.search.documents.indexes.aio import SearchIndexClient
from azure.search.documents.indexes.models import SearchIndex
from azure.search.documents.models import VectorizableTextQuery, VectorizedQuery
from pydantic import ValidationError

from semantic_kernel.connectors.memory.azure_ai_search.utils import (
    data_model_definition_to_azure_ai_search_index,
    get_search_client,
    get_search_index_client,
)
from semantic_kernel.data.record_definition import VectorStoreRecordDefinition, VectorStoreRecordVectorField
from semantic_kernel.data.text_search import AnyTagsEqualTo, EqualTo, KernelSearchResults
from semantic_kernel.data.vector_search import (
    VectorizableTextSearchMixin,
    VectorizedSearchMixin,
    VectorSearchFilter,
    VectorSearchOptions,
    VectorSearchResult,
    VectorTextSearchMixin,
)
from semantic_kernel.data.vector_storage import TKey, TModel, VectorStoreRecordCollection
from semantic_kernel.exceptions import (
    VectorSearchExecutionException,
    VectorStoreInitializationException,
    VectorStoreOperationException,
)
from semantic_kernel.utils.feature_stage_decorator import experimental

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class AzureAISearchCollection(
    VectorStoreRecordCollection[TKey, TModel],
    VectorizableTextSearchMixin[TKey, TModel],
    VectorizedSearchMixin[TKey, TModel],
    VectorTextSearchMixin[TKey, TModel],
    Generic[TKey, TModel],
):
    """Azure AI Search collection implementation."""

    search_client: SearchClient
    search_index_client: SearchIndexClient
    supported_key_types: ClassVar[list[str] | None] = ["str"]
    supported_vector_types: ClassVar[list[str] | None] = ["float", "int"]
    managed_search_index_client: bool = True

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
                raise VectorStoreInitializationException(
                    "Search client and search index client have different index names."
                )
            super().__init__(
                data_model_type=data_model_type,
                data_model_definition=data_model_definition,
                collection_name=collection_name,
                search_client=search_client,
                search_index_client=search_index_client,
                managed_search_index_client=False,
                managed_client=False,
            )
            return

        if search_index_client:
            if not collection_name:
                raise VectorStoreInitializationException("Collection name is required.")
            super().__init__(
                data_model_type=data_model_type,
                data_model_definition=data_model_definition,
                collection_name=collection_name,
                search_client=get_search_client(
                    search_index_client=search_index_client, collection_name=collection_name
                ),
                search_index_client=search_index_client,
                managed_search_index_client=False,
            )
            return

        from semantic_kernel.connectors.memory.azure_ai_search.azure_ai_search_settings import (
            AzureAISearchSettings,
        )

        try:
            azure_ai_search_settings = AzureAISearchSettings(
                env_file_path=kwargs.get("env_file_path"),
                endpoint=kwargs.get("search_endpoint"),
                api_key=kwargs.get("api_key"),
                env_file_encoding=kwargs.get("env_file_encoding"),
                index_name=collection_name,
            )
        except ValidationError as exc:
            raise VectorStoreInitializationException("Failed to create Azure Cognitive Search settings.") from exc
        search_index_client = get_search_index_client(
            azure_ai_search_settings=azure_ai_search_settings,
            azure_credential=kwargs.get("azure_credentials"),
            token_credential=kwargs.get("token_credentials"),
        )
        if not azure_ai_search_settings.index_name:
            raise VectorStoreInitializationException("Collection name is required.")

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
    ) -> Sequence[TKey]:
        if not isinstance(records, list):
            records = list(records)
        results = await self.search_client.merge_or_upload_documents(documents=records, **kwargs)
        return [result.key for result in results]  # type: ignore

    @override
    async def _inner_get(self, keys: Sequence[TKey], **kwargs: Any) -> Sequence[dict[str, Any]]:
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
            *[client.get_document(key=key, selected_fields=selected_fields) for key in keys],  # type: ignore
            return_exceptions=True,
        )
        return [res for res in result if not isinstance(res, BaseException)]

    @override
    async def _inner_delete(self, keys: Sequence[TKey], **kwargs: Any) -> None:
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
            raise VectorStoreOperationException("Invalid index type supplied, should be a SearchIndex object.")
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

    @override
    async def _inner_search(
        self,
        options: VectorSearchOptions,
        search_text: str | None = None,
        vectorizable_text: str | None = None,
        vector: list[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        search_args: dict[str, Any] = {
            "top": options.top,
            "skip": options.skip,
            "include_total_count": options.include_total_count,
        }
        if options.filter.filters:
            search_args["filter"] = self._build_filter_string(options.filter)
        if search_text is not None:
            search_args["search_text"] = search_text
        if vectorizable_text is not None:
            search_args["vector_queries"] = [
                VectorizableTextQuery(
                    text=vectorizable_text,
                    k_nearest_neighbors=options.top,
                    fields=options.vector_field_name,
                )
            ]
        if vector is not None:
            search_args["vector_queries"] = [
                VectorizedQuery(
                    vector=vector,
                    k_nearest_neighbors=options.top,
                    fields=options.vector_field_name,
                )
            ]
        if "vector_queries" not in search_args and "search_text" not in search_args:
            # this assumes that a filter only query is asked for
            search_args["search_text"] = "*"

        if options.include_vectors:
            search_args["select"] = ["*"]
        else:
            search_args["select"] = [
                name
                for name, field in self.data_model_definition.fields.items()
                if not isinstance(field, VectorStoreRecordVectorField)
            ]
        try:
            raw_results = await self.search_client.search(**search_args)
        except Exception as exc:
            raise VectorSearchExecutionException("Failed to search the collection.") from exc
        return KernelSearchResults(
            results=self._get_vector_search_results_from_results(raw_results, options),
            total_count=await raw_results.get_count() if options.include_total_count else None,
        )

    def _build_filter_string(self, search_filter: VectorSearchFilter) -> str:
        """Create the filter string based on the filters.

        Since the group_type is always added (and currently always "AND"), the last " and " is removed.
        """
        filter_string = ""
        for filter in search_filter.filters:
            if isinstance(filter, EqualTo):
                filter_string += f"{filter.field_name} eq '{filter.value}' {search_filter.group_type.lower()} "
            elif isinstance(filter, AnyTagsEqualTo):
                filter_string += (
                    f"{filter.field_name}/any(t: t eq '{filter.value}') {search_filter.group_type.lower()} "
                )
        if filter_string.endswith(" and "):
            filter_string = filter_string[:-5]
        return filter_string

    @override
    def _get_record_from_result(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    @override
    def _get_score_from_result(self, result: dict[str, Any]) -> float | None:
        return result.get("@search.score")

    @override
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager."""
        if self.managed_client:
            await self.search_client.close()
        if self.managed_search_index_client:
            await self.search_index_client.close()
