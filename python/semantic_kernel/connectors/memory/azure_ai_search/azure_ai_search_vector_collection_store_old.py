# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Any, TypeVar

from azure.core.credentials import AzureKeyCredential, TokenCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.indexes.aio import SearchIndexClient
from azure.search.documents.indexes.models import (
    ExhaustiveKnnAlgorithmConfiguration,
    ExhaustiveKnnParameters,
    HnswAlgorithmConfiguration,
    HnswParameters,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SearchResourceEncryptionKey,
    SimpleField,
    VectorSearch,
    VectorSearchAlgorithmMetric,
    VectorSearchProfile,
)
from pydantic import ValidationError

from semantic_kernel.connectors.memory.azure_ai_search.azure_ai_search_vector_store_collection import (
    AzureAISearchVectorStoreCollection,
)
from semantic_kernel.connectors.memory.azure_ai_search.utils import get_search_index_async_client
from semantic_kernel.data.models.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.models.vector_store_record_fields import (
    DistanceFunction,
    IndexKind,
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.exceptions import MemoryConnectorInitializationError
from semantic_kernel.exceptions.memory_connector_exceptions import MemoryConnectorException
from semantic_kernel.kernel import Kernel
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)

TModel = TypeVar("TModel")

INDEX_ALGORITHM_MAP = {
    IndexKind.hnsw: (HnswAlgorithmConfiguration, HnswParameters),
    IndexKind.flat: (ExhaustiveKnnAlgorithmConfiguration, ExhaustiveKnnParameters),
    "default": (HnswAlgorithmConfiguration, HnswParameters),
}

DISTANCE_FUNCTION_MAP = {
    DistanceFunction.cosine: VectorSearchAlgorithmMetric.COSINE,
    DistanceFunction.dot_prod: VectorSearchAlgorithmMetric.DOT_PRODUCT,
    DistanceFunction.euclidean: VectorSearchAlgorithmMetric.EUCLIDEAN,
    "default": VectorSearchAlgorithmMetric.COSINE,
}

TYPE_MAPPER_DATA = {
    "str": SearchFieldDataType.String,
    "int": SearchFieldDataType.Int64,
    "float": SearchFieldDataType.Double,
    "bool": SearchFieldDataType.Boolean,
    "list[str]": SearchFieldDataType.Collection(SearchFieldDataType.String),
    "list[int]": SearchFieldDataType.Collection(SearchFieldDataType.Int64),
    "list[float]": SearchFieldDataType.Collection(SearchFieldDataType.Double),
    "list[bool]": SearchFieldDataType.Collection(SearchFieldDataType.Boolean),
    "default": SearchFieldDataType.String,
}

TYPE_MAPPER_VECTOR = {
    "list[float]": SearchFieldDataType.Collection(SearchFieldDataType.Single),
    "list[int]": "Collection(Edm.Int16)",
    "list[binary]": "Collection(Edm.Byte)",
    "default": SearchFieldDataType.Collection(SearchFieldDataType.Single),
}


@experimental_class
class AzureAISearchVectorStore(AzureAISearchVectorStoreCollection):
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

    async def list_collection_names(self, **kwargs: Any) -> list[str]:
        """Get the names of all collections."""
        if "params" not in kwargs:
            kwargs["params"] = {"select": ["name"]}
        return [index async for index in self._search_index_client.list_index_names(**kwargs)]

    async def collection_exists(self, collection_name: str | None = None, **kwargs) -> bool:
        """Check if a collection with the name exists."""
        return self._get_collection_name(collection_name) in await self.list_collection_names(**kwargs)

    async def delete_collection(self, collection_name: str | None = None, **kwargs) -> None:
        """Delete a collection."""
        await self._search_index_client.delete_index(index=self._get_collection_name(collection_name), **kwargs)

    async def create_collection(
        self, collection_name: str | None = None, definition: VectorStoreRecordDefinition | None = None, **kwargs
    ) -> SearchIndex:
        """Create a new collection in Azure AI Search.

        Args:
            collection_name (str): The name of the collection.
            definition (VectorStoreRecordDefinition): The definition to use to create an index,
                if supplied this takes precedence over the definition set in the constructor.
            **kwargs: Additional keyword arguments.
                index (SearchIndex): The search index to create, if this is supplied
                    this is used instead of the index created based on the definition.
                encryption_key (SearchResourceEncryptionKey): The encryption key to use,
                    not used when index is supplied.
                other kwargs are passed to the create_index method.
        """
        if index := kwargs.pop("index", None):
            if isinstance(index, SearchIndex):
                return await self._search_index_client.create_index(index=index, **kwargs)
            raise MemoryConnectorException("Invalid index type.")
        if not definition and not self._data_model_definition:
            raise MemoryConnectorInitializationError("Definition is required to create a collection.")
        index = self._data_model_to_index(
            collection_name=self._get_collection_name(collection_name),
            definition=definition or self._data_model_definition,
            encryption_key=kwargs.pop("encryption_key", None),
        )
        return await self._search_index_client.create_index(index=index, **kwargs)

    def _data_model_to_index(
        self,
        collection_name: str,
        definition: VectorStoreRecordDefinition,
        encryption_key: SearchResourceEncryptionKey | None = None,
    ) -> SearchIndex:
        fields = []
        search_profiles = []
        search_algos = []

        for field in definition.fields.values():
            if isinstance(field, VectorStoreRecordDataField):
                if not field.property_type:
                    logger.debug(f"Field {field.name} has not specified type, defaulting to Edm.String.")
                type_ = TYPE_MAPPER_DATA[field.property_type or "default"]
                fields.append(
                    SearchField(
                        name=field.name,
                        type=type_,
                        filterable=field.is_filterable,
                        searchable=type_ in ("Edm.String", "Collection(Edm.String)"),
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
                algo_class, algo_params = INDEX_ALGORITHM_MAP[field.index_kind or "default"]
                search_algos.append(
                    algo_class(
                        name=algo_name,
                        parameters=algo_params(
                            metric=DISTANCE_FUNCTION_MAP[field.distance_function or "default"],
                        ),
                    )
                )
        return SearchIndex(
            name=collection_name,
            fields=fields,
            vector_search=VectorSearch(profiles=search_profiles, algorithms=search_algos),
            encryption_key=encryption_key,
        )
