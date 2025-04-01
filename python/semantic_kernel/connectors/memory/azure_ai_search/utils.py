# Copyright (c) Microsoft. All rights reserved.

import asyncio
import contextlib
import logging
from typing import TYPE_CHECKING, Any

from azure.core.credentials import AzureKeyCredential, TokenCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.indexes.aio import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchField,
    SearchIndex,
    SearchResourceEncryptionKey,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)

from semantic_kernel.connectors.memory.azure_ai_search.azure_ai_search_settings import AzureAISearchSettings
from semantic_kernel.connectors.memory.azure_ai_search.const import (
    DISTANCE_FUNCTION_MAP,
    INDEX_ALGORITHM_MAP,
    TYPE_MAPPER_DATA,
    TYPE_MAPPER_VECTOR,
)
from semantic_kernel.data.record_definition import (
    VectorStoreRecordDataField,
    VectorStoreRecordDefinition,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.exceptions import ServiceInitializationError
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.telemetry.user_agent import APP_INFO, prepend_semantic_kernel_to_user_agent

if TYPE_CHECKING:
    from azure.core.credentials_async import AsyncTokenCredential

logger: logging.Logger = logging.getLogger(__name__)


def get_search_client(search_index_client: SearchIndexClient, collection_name: str, **kwargs: Any) -> SearchClient:
    """Create a search client for a collection."""
    return SearchClientWrapper(
        search_index_client._endpoint, collection_name, search_index_client._credential, **kwargs
    )


def get_search_index_client(
    azure_ai_search_settings: AzureAISearchSettings,
    azure_credential: AzureKeyCredential | None = None,
    token_credential: "AsyncTokenCredential | TokenCredential | None" = None,
) -> SearchIndexClient:
    """Return a client for Azure Cognitive Search.

    Args:
        azure_ai_search_settings (AzureAISearchSettings): Azure Cognitive Search settings.
        azure_credential (AzureKeyCredential): Optional Azure credentials (default: {None}).
        token_credential (TokenCredential): Optional Token credential (default: {None}).
    """
    # Credentials
    credential: "AzureKeyCredential | AsyncTokenCredential | TokenCredential | None" = None
    if azure_ai_search_settings.api_key:
        credential = AzureKeyCredential(azure_ai_search_settings.api_key.get_secret_value())
    elif azure_credential:
        credential = azure_credential
    elif token_credential:
        credential = token_credential
    else:
        raise ServiceInitializationError("Error: missing Azure AI Search client credentials.")

    return SearchIndexClientWrapper(
        endpoint=str(azure_ai_search_settings.endpoint),
        credential=credential,  # type: ignore
        headers=prepend_semantic_kernel_to_user_agent({}) if APP_INFO else None,
    )


@experimental
def data_model_definition_to_azure_ai_search_index(
    collection_name: str,
    definition: VectorStoreRecordDefinition,
    encryption_key: SearchResourceEncryptionKey | None = None,
) -> SearchIndex:
    """Convert a VectorStoreRecordDefinition to an Azure AI Search index."""
    fields = []
    search_profiles = []
    search_algos = []

    for field in definition.fields.values():
        if isinstance(field, VectorStoreRecordDataField):
            assert field.name  # nosec
            if not field.property_type:
                logger.debug(f"Field {field.name} has not specified type, defaulting to Edm.String.")
            type_ = TYPE_MAPPER_DATA[field.property_type or "default"]
            fields.append(
                SearchField(
                    name=field.name,
                    type=type_,
                    filterable=field.is_filterable,
                    # searchable is set first on the value of is_full_text_searchable,
                    # if it is None it checks the field type, if text then it is searchable
                    searchable=type_ in ("Edm.String", "Collection(Edm.String)")
                    if field.is_full_text_searchable is None
                    else field.is_full_text_searchable,
                    sortable=True,
                    hidden=False,
                )
            )
        elif isinstance(field, VectorStoreRecordKeyField):
            assert field.name  # nosec
            fields.append(
                SimpleField(
                    name=field.name,
                    type="Edm.String",  # hardcoded, only allowed type for key
                    key=True,
                    filterable=True,
                    searchable=True,
                )
            )
        elif isinstance(field, VectorStoreRecordVectorField):
            assert field.name  # nosec
            if not field.property_type:
                logger.debug(f"Field {field.name} has not specified type, defaulting to Collection(Edm.Single).")
            if not field.index_kind:
                logger.debug(f"Field {field.name} has not specified index kind, defaulting to hnsw.")
            if not field.distance_function:
                logger.debug(f"Field {field.name} has not specified distance function, defaulting to cosine.")
            profile_name = f"{field.name}_profile"
            algo_name = f"{field.name}_algorithm"
            fields.append(
                SearchField(
                    name=field.name,
                    type=TYPE_MAPPER_VECTOR[field.property_type or "default"],
                    searchable=True,
                    vector_search_dimensions=field.dimensions,
                    vector_search_profile_name=profile_name,
                    hidden=False,
                )
            )
            search_profiles.append(
                VectorSearchProfile(
                    name=profile_name,
                    algorithm_configuration_name=algo_name,
                )
            )
            try:
                algo_class, algo_params = INDEX_ALGORITHM_MAP[field.index_kind or "default"]
            except KeyError as e:
                raise ServiceInitializationError(f"Error: {field.index_kind} not found in INDEX_ALGORITHM_MAP.") from e
            try:
                distance_metric = DISTANCE_FUNCTION_MAP[field.distance_function or "default"]
            except KeyError as e:
                raise ServiceInitializationError(
                    f"Error: {field.distance_function} not found in DISTANCE_FUNCTION_MAP."
                ) from e
            search_algos.append(
                algo_class(
                    name=algo_name,
                    parameters=algo_params(
                        metric=distance_metric,
                    ),
                )
            )
    return SearchIndex(
        name=collection_name,
        fields=fields,
        vector_search=VectorSearch(profiles=search_profiles, algorithms=search_algos),
        encryption_key=encryption_key,
    )


class SearchIndexClientWrapper(SearchIndexClient):
    """Wrapper to make sure the connection is closed when the object is deleted."""

    def __del__(self) -> None:
        """Async close connection, done when the object is deleted, used when SK creates a client."""
        with contextlib.suppress(Exception):
            asyncio.get_running_loop().create_task(self.close())


class SearchClientWrapper(SearchClient):
    """Wrapper to make sure the connection is closed when the object is deleted."""

    def __del__(self) -> None:
        """Async close connection, done when the object is deleted, used when SK creates a client."""
        with contextlib.suppress(Exception):
            asyncio.get_running_loop().create_task(self.close())
