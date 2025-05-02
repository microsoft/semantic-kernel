# Copyright (c) Microsoft. All rights reserved.

import ast
import asyncio
import logging
import sys
from collections.abc import Sequence
from typing import Any, ClassVar, Final, Generic, TypeVar

from azure.core.credentials import AzureKeyCredential, TokenCredential
from azure.core.credentials_async import AsyncTokenCredential
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
    VectorSearchAlgorithmMetric,
    VectorSearchProfile,
)
from azure.search.documents.indexes.models import VectorSearch as AZSVectorSearch
from azure.search.documents.models import VectorizableTextQuery, VectorizedQuery
from pydantic import SecretStr, ValidationError

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.data.const import DistanceFunction, IndexKind
from semantic_kernel.data.record_definition import (
    VectorStoreRecordDataField,
    VectorStoreRecordDefinition,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.data.text_search import KernelSearchResults
from semantic_kernel.data.vector_search import SearchType, VectorSearch, VectorSearchOptions, VectorSearchResult
from semantic_kernel.data.vector_storage import (
    GetFilteredRecordOptions,
    TModel,
    VectorStore,
    VectorStoreRecordCollection,
    _get_collection_name_from_model,
)
from semantic_kernel.exceptions import (
    ServiceInitializationError,
    VectorSearchExecutionException,
    VectorStoreInitializationException,
    VectorStoreOperationException,
)
from semantic_kernel.kernel_pydantic import HttpsUrl, KernelBaseSettings
from semantic_kernel.utils.feature_stage_decorator import release_candidate
from semantic_kernel.utils.telemetry.user_agent import APP_INFO, prepend_semantic_kernel_to_user_agent

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

logger: logging.Logger = logging.getLogger(__name__)


TKey = TypeVar("TKey", bound=str)

INDEX_ALGORITHM_MAP: Final[dict[IndexKind, tuple[type, type]]] = {
    IndexKind.HNSW: (HnswAlgorithmConfiguration, HnswParameters),
    IndexKind.FLAT: (ExhaustiveKnnAlgorithmConfiguration, ExhaustiveKnnParameters),
    IndexKind.DEFAULT: (HnswAlgorithmConfiguration, HnswParameters),
}
DISTANCE_FUNCTION_MAP: Final[dict[DistanceFunction, VectorSearchAlgorithmMetric]] = {
    DistanceFunction.COSINE_DISTANCE: VectorSearchAlgorithmMetric.COSINE,
    DistanceFunction.DOT_PROD: VectorSearchAlgorithmMetric.DOT_PRODUCT,
    DistanceFunction.EUCLIDEAN_DISTANCE: VectorSearchAlgorithmMetric.EUCLIDEAN,
    DistanceFunction.HAMMING: VectorSearchAlgorithmMetric.HAMMING,
    DistanceFunction.DEFAULT: VectorSearchAlgorithmMetric.COSINE,
}
TYPE_MAP_DATA: Final[dict[str, str]] = {
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

TYPE_MAP_VECTOR: Final[dict[str, str]] = {
    "float": SearchFieldDataType.Collection(SearchFieldDataType.Single),
    "int": "Collection(Edm.Int16)",
    "binary": "Collection(Edm.Byte)",
    "default": SearchFieldDataType.Collection(SearchFieldDataType.Single),
}

__all__ = [
    "AzureAISearchCollection",
    "AzureAISearchSettings",
    "AzureAISearchStore",
]


@release_candidate
class AzureAISearchSettings(KernelBaseSettings):
    """Azure AI Search model settings currently used by the AzureCognitiveSearchMemoryStore connector.

    Args:
    - api_key: SecretStr - Azure AI Search API key (Env var AZURE_AI_SEARCH_API_KEY)
    - endpoint: HttpsUrl - Azure AI Search endpoint (Env var AZURE_AI_SEARCH_ENDPOINT)
    - index_name: str - Azure AI Search index name (Env var AZURE_AI_SEARCH_INDEX_NAME)
    """

    env_prefix: ClassVar[str] = "AZURE_AI_SEARCH_"

    api_key: SecretStr | None = None
    endpoint: HttpsUrl
    index_name: str | None = None


def _get_search_client(search_index_client: SearchIndexClient, collection_name: str, **kwargs: Any) -> SearchClient:
    """Create a search client for a collection."""
    return SearchClient(search_index_client._endpoint, collection_name, search_index_client._credential, **kwargs)


def _get_search_index_client(
    azure_ai_search_settings: AzureAISearchSettings,
    azure_credential: AzureKeyCredential | None = None,
    token_credential: "AsyncTokenCredential | TokenCredential | None" = None,
) -> SearchIndexClient:
    """Return a client for Azure Cognitive Search.

    Args:
        azure_ai_search_settings: Azure Cognitive Search settings.
        azure_credential: Optional Azure credentials (default: {None}).
        token_credential: Optional Token credential (default: {None}).
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

    return SearchIndexClient(
        endpoint=str(azure_ai_search_settings.endpoint),
        credential=credential,  # type: ignore
        headers=prepend_semantic_kernel_to_user_agent({}) if APP_INFO else None,
    )


def _data_model_definition_to_azure_ai_search_index(
    collection_name: str,
    definition: VectorStoreRecordDefinition,
    encryption_key: SearchResourceEncryptionKey | None = None,
) -> SearchIndex:
    """Convert a VectorStoreRecordDefinition to an Azure AI Search index."""
    fields = []
    search_profiles = []
    search_algos = []

    for field in definition.fields:
        if isinstance(field, VectorStoreRecordDataField):
            if not field.property_type:
                logger.debug(f"Field {field.name} has not specified type, defaulting to Edm.String.")
            type_ = TYPE_MAP_DATA[field.property_type or "default"]
            fields.append(
                SearchField(
                    name=field.storage_property_name or field.name,
                    type=type_,
                    filterable=field.is_indexed or field.is_full_text_indexed,
                    # searchable is set first on the value of is_full_text_searchable,
                    # if it is None it checks the field type, if text then it is searchable
                    searchable=type_ in ("Edm.String", "Collection(Edm.String)")
                    if field.is_full_text_indexed is None
                    else field.is_full_text_indexed,
                    sortable=True,
                    hidden=False,
                )
            )
        elif isinstance(field, VectorStoreRecordKeyField):
            fields.append(
                SimpleField(
                    name=field.storage_property_name or field.name,
                    type="Edm.String",  # hardcoded, only allowed type for key
                    key=True,
                    filterable=True,
                    searchable=True,
                )
            )
        elif isinstance(field, VectorStoreRecordVectorField):
            if not field.property_type:
                logger.debug(f"Field {field.name} has not specified type, defaulting to Collection(Edm.Single).")
            if field.index_kind not in INDEX_ALGORITHM_MAP:
                raise VectorStoreOperationException(f"{field.index_kind} not supported in Azure AI Search.")
            if field.distance_function not in DISTANCE_FUNCTION_MAP:
                raise VectorStoreOperationException(f"{field.distance_function} not supported in Azure AI Search.")

            profile_name = f"{field.storage_property_name or field.name}_profile"
            algo_name = f"{field.storage_property_name or field.name}_algorithm"
            fields.append(
                SearchField(
                    name=field.storage_property_name or field.name,
                    type=TYPE_MAP_VECTOR[field.property_type or "default"],
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
            algo_class, algo_params = INDEX_ALGORITHM_MAP[field.index_kind]
            distance_metric = DISTANCE_FUNCTION_MAP[field.distance_function]
            search_algos.append(algo_class(name=algo_name, parameters=algo_params(metric=distance_metric)))
    return SearchIndex(
        name=collection_name,
        fields=fields,
        vector_search=AZSVectorSearch(profiles=search_profiles, algorithms=search_algos),
        encryption_key=encryption_key,
    )


@release_candidate
class AzureAISearchCollection(
    VectorStoreRecordCollection[TKey, TModel],
    VectorSearch[TKey, TModel],
    Generic[TKey, TModel],
):
    """Azure AI Search collection implementation."""

    search_client: SearchClient
    search_index_client: SearchIndexClient
    supported_key_types: ClassVar[set[str] | None] = {"str"}
    supported_vector_types: ClassVar[set[str] | None] = {"float", "int"}
    supported_search_types: ClassVar[set[SearchType]] = {SearchType.VECTOR, SearchType.KEYWORD_HYBRID}
    managed_search_index_client: bool = True

    def __init__(
        self,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        collection_name: str | None = None,
        search_index_client: SearchIndexClient | None = None,
        search_client: SearchClient | None = None,
        embedding_generator: "EmbeddingGeneratorBase | None" = None,
        **kwargs: Any,
    ) -> None:
        """Initializes a new instance of the AzureAISearchCollection class.

        The collection name can be set in four ways:
        1. By passing it in the constructor.
        2. By passing it in the data model definition or data_model_type.
        3. By passing it in the search client.
        4. By setting the AZURE_AI_SEARCH_INDEX_NAME environment variable.

        They are checked in that order, so if the collection name is passed in the constructor it is used.

        Args:
            data_model_type: The type of the data model.
            data_model_definition: The model definition, optional.
            collection_name: The name of the collection, optional.
            search_index_client: The search index client for interacting with Azure AI Search,
                used for creating and deleting indexes.
            search_client: The search client for interacting with Azure AI Search,
                used for record operations.
            embedding_generator: The embedding generator, optional.
            **kwargs: Additional keyword arguments, including:
                The same keyword arguments used for AzureAISearchVectorStore:
                    search_endpoint: str | None = None,
                    api_key: str | None = None,
                    azure_credentials: AzureKeyCredential | None = None,
                    token_credentials: AsyncTokenCredential | TokenCredential | None = None,
                    env_file_path: str | None = None,
                    env_file_encoding: str | None = None

        """
        if not collection_name:
            collection_name = _get_collection_name_from_model(data_model_type, data_model_definition)
        if not collection_name and search_client:
            collection_name = search_client._index_name
        assert collection_name  # nosec
        if search_client and search_index_client:
            if collection_name and search_client._index_name != collection_name:
                search_client._index_name = collection_name
            super().__init__(
                data_model_type=data_model_type,
                data_model_definition=data_model_definition,
                collection_name=collection_name,
                search_client=search_client,
                search_index_client=search_index_client,
                managed_search_index_client=False,
                managed_client=False,
                embedding_generator=embedding_generator,
            )
            return

        if search_index_client:
            super().__init__(
                data_model_type=data_model_type,
                data_model_definition=data_model_definition,
                collection_name=collection_name,
                search_client=_get_search_client(
                    search_index_client=search_index_client, collection_name=collection_name
                ),
                search_index_client=search_index_client,
                managed_search_index_client=False,
                embedding_generator=embedding_generator,
            )
            return

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
        search_index_client = _get_search_index_client(
            azure_ai_search_settings=azure_ai_search_settings,
            azure_credential=kwargs.get("azure_credentials"),
            token_credential=kwargs.get("token_credentials"),
        )
        super().__init__(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=azure_ai_search_settings.index_name,
            search_client=_get_search_client(
                search_index_client=search_index_client,
                collection_name=azure_ai_search_settings.index_name,  # type: ignore
            ),
            search_index_client=search_index_client,
            embedding_generator=embedding_generator,
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
    async def _inner_get(
        self,
        keys: Sequence[TKey] | None = None,
        options: GetFilteredRecordOptions | None = None,
        **kwargs: Any,
    ) -> Sequence[dict[str, Any]]:
        client = self.search_client
        if "selected_fields" in kwargs:
            selected_fields = kwargs["selected_fields"]
        elif kwargs.get("include_vectors"):
            selected_fields = ["*"]
        else:
            selected_fields = self.data_model_definition.get_storage_property_names(include_vector_fields=False)
        if keys is not None:
            gather_result = await asyncio.gather(
                *[client.get_document(key=key, selected_fields=selected_fields) for key in keys],  # type: ignore
                return_exceptions=True,
            )
            return [res for res in gather_result if not isinstance(res, BaseException)]
        if options is not None:
            ordering = []
            if options.order_by:
                order_by = options.order_by if isinstance(options.order_by, Sequence) else [options.order_by]
                for order in order_by:
                    if order.field not in self.data_model_definition.fields:
                        logger.warning(f"Field {order.field} not in data model, skipping.")
                        continue
                    ordering.append(order.field if order.ascending else f"{order.field} desc")

            result = await client.search(
                search_text="*",
                top=options.top,
                skip=options.skip,
                select=selected_fields,
                order_by=ordering,
            )
            return [res async for res in result]
        raise VectorStoreOperationException("No keys or options provided for get operation.")

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
            index=_data_model_definition_to_azure_ai_search_index(
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
        search_type: SearchType,
        options: VectorSearchOptions,
        values: Any | None = None,
        vector: Sequence[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        search_args: dict[str, Any] = {
            "top": options.top,
            "skip": options.skip,
            "include_total_count": options.include_total_count,
        }
        if options.include_vectors:
            search_args["select"] = ["*"]
        else:
            search_args["select"] = self.data_model_definition.get_storage_property_names(include_vector_fields=False)
        if filter := self._build_filter(options.filter):
            search_args["filter"] = filter if isinstance(filter, str) else " and ".join(filter)
        match search_type:
            case SearchType.VECTOR:
                if vector is not None:
                    vector_field = self.data_model_definition.try_get_vector_field(options.vector_field_name)
                    search_args["vector_queries"] = [
                        VectorizedQuery(
                            vector=vector,  # type: ignore
                            fields=vector_field.name if vector_field else None,
                        )
                    ]
                elif values is not None:
                    generated_vector = await self._generate_vector_from_values(values, options)
                    vector_field = self.data_model_definition.try_get_vector_field(options.vector_field_name)
                    if generated_vector is not None:
                        search_args["vector_queries"] = [
                            VectorizedQuery(
                                vector=generated_vector,  # type: ignore
                                fields=vector_field.name if vector_field else None,
                            )
                        ]
                    else:
                        search_args["vector_queries"] = [
                            VectorizableTextQuery(
                                text=values,
                                fields=vector_field.name if vector_field else None,
                            )
                        ]
                else:
                    raise VectorStoreOperationException("No vector or keywords provided for vector search.")
            case SearchType.KEYWORD_HYBRID:
                if values is None:
                    raise VectorStoreOperationException("No vector and/or keywords provided for search.")
                vector_field = self.data_model_definition.try_get_vector_field(options.vector_field_name)
                search_args["search_fields"] = (
                    [options.keyword_field_name]
                    if options.keyword_field_name is not None
                    else [
                        field.name
                        for field in self.data_model_definition.fields
                        if isinstance(field, VectorStoreRecordDataField) and field.is_full_text_indexed
                    ]
                )
                if not search_args["search_fields"]:
                    raise VectorStoreOperationException("No searchable fields found for hybrid search.")
                search_args["search_text"] = values

                vector = await self._generate_vector_from_values(values, options) if vector is None else vector
                if vector is not None:
                    search_args["vector_queries"] = [
                        VectorizedQuery(
                            vector=vector,  # type: ignore
                            fields=vector_field.name if vector_field else None,
                        )
                    ]
                else:
                    search_args["vector_queries"] = [
                        VectorizableTextQuery(
                            text=values,
                            fields=vector_field.name if vector_field else None,
                        )
                    ]
        try:
            raw_results = await self.search_client.search(**search_args, **kwargs)
        except Exception as exc:
            raise VectorSearchExecutionException("Failed to search the collection.") from exc
        return KernelSearchResults(
            results=self._get_vector_search_results_from_results(raw_results, options),
            total_count=await raw_results.get_count() if options.include_total_count else None,
        )

    @override
    def _lambda_parser(self, node: ast.AST) -> Any:
        match node:
            case ast.Compare():
                if len(node.ops) > 1:
                    values: list[ast.expr] = []
                    for idx in range(len(node.ops)):
                        if idx == 0:
                            values.append(
                                ast.Compare(
                                    left=node.left,
                                    ops=[node.ops[idx]],
                                    comparators=[node.comparators[idx]],
                                )
                            )
                        else:
                            values.append(
                                ast.Compare(
                                    left=node.comparators[idx - 1],
                                    ops=[node.ops[idx]],
                                    comparators=[node.comparators[idx]],
                                )
                            )
                    return self._lambda_parser(ast.BoolOp(op=ast.And(), values=values))
                left = self._lambda_parser(node.left)
                right = self._lambda_parser(node.comparators[0])
                op = node.ops[0]
                match op:
                    case ast.In():
                        return f"search.ismatch({left}, '{right}')"
                    case ast.NotIn():
                        return f"not search.ismatch({left}, '{right}')"
                    case ast.Eq():
                        return f"{left} eq {right}"
                    case ast.NotEq():
                        return f"{left} ne {right}"
                    case ast.Gt():
                        return f"{left} gt {right}"
                    case ast.GtE():
                        return f"{left} ge {right}"
                    case ast.Lt():
                        return f"{left} lt {right}"
                    case ast.LtE():
                        return f"{left} le {right}"
                raise NotImplementedError(f"Unsupported operator: {type(op)}")
            case ast.BoolOp():
                op_str = "and" if isinstance(node.op, ast.And) else "or"
                return "(" + f" {op_str} ".join([self._lambda_parser(v) for v in node.values]) + ")"
            case ast.UnaryOp():
                match node.op:
                    case ast.UAdd():
                        return f"+{self._lambda_parser(node.operand)}"
                    case ast.USub():
                        return f"-{self._lambda_parser(node.operand)}"
                    case ast.Invert():
                        raise NotImplementedError("Invert operation is not supported.")
                    case ast.Not():
                        return f"not {self._lambda_parser(node.operand)}"
            case ast.Attribute():
                # Check if attribute is in data model
                if node.attr not in self.data_model_definition.storage_property_names:
                    raise VectorStoreOperationException(
                        f"Field '{node.attr}' not in data model (storage property names are used)."
                    )
                return node.attr
            case ast.Name():
                raise NotImplementedError("Constants are not supported, make sure to use a value or a attribute.")
            case ast.Constant():
                return str(node.value) if isinstance(node.value, float | int) else f"'{node.value}'"
        raise NotImplementedError(f"Unsupported AST node: {type(node)}")

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


@release_candidate
class AzureAISearchStore(VectorStore):
    """Azure AI Search store implementation."""

    search_index_client: SearchIndexClient

    def __init__(
        self,
        search_endpoint: str | None = None,
        api_key: str | None = None,
        azure_credentials: "AzureKeyCredential | None" = None,
        token_credentials: "AsyncTokenCredential | TokenCredential | None" = None,
        search_index_client: SearchIndexClient | None = None,
        embedding_generator: "EmbeddingGeneratorBase | None" = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initializes a new instance of the AzureAISearchStore class."""
        managed_client: bool = False
        if not search_index_client:
            try:
                azure_ai_search_settings = AzureAISearchSettings(
                    env_file_path=env_file_path,
                    endpoint=search_endpoint,
                    api_key=api_key,
                    env_file_encoding=env_file_encoding,
                )
            except ValidationError as exc:
                raise VectorStoreInitializationException("Failed to create Azure AI Search settings.") from exc
            search_index_client = _get_search_index_client(
                azure_ai_search_settings=azure_ai_search_settings,
                azure_credential=azure_credentials,
                token_credential=token_credentials,
            )
            managed_client = True

        super().__init__(
            search_index_client=search_index_client,
            managed_client=managed_client,
            embedding_generator=embedding_generator,
        )

    @override
    def get_collection(
        self,
        data_model_type: type[TModel],
        *,
        data_model_definition: VectorStoreRecordDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        search_client: SearchClient | None = None,
        **kwargs: Any,
    ) -> "VectorStoreRecordCollection":
        """Get a AzureAISearchCollection tied to a collection.

        Args:
            collection_name: The name of the collection.
            data_model_type: The type of the data model.
            data_model_definition: The model fields, optional.
            search_client: The search client for interacting with Azure AI Search,
                will be created if not supplied.
            embedding_generator: The embedding generator, optional.
            **kwargs: Additional keyword arguments, passed to the collection constructor.
        """
        return AzureAISearchCollection(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=collection_name,
            search_index_client=self.search_index_client,
            search_client=search_client,
            embedding_generator=embedding_generator or self.embedding_generator,
            **kwargs,
        )

    @override
    async def list_collection_names(self, **kwargs: Any) -> list[str]:
        if "params" not in kwargs:
            kwargs["params"] = {"select": ["name"]}
        return [index async for index in self.search_index_client.list_index_names(**kwargs)]

    @override
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager."""
        if self.managed_client:
            await self.search_index_client.close()
