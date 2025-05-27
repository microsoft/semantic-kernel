# Copyright (c) Microsoft. All rights reserved.

import ast
import json
import logging
import sys
from collections.abc import Callable, Sequence
from typing import Any, ClassVar, Final, Generic, TypeVar

from pydantic import SecretStr, field_validator, model_validator
from weaviate import WeaviateAsyncClient, use_async_with_embedded, use_async_with_local, use_async_with_weaviate_cloud
from weaviate.classes.config import Configure, DataType, Property
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter, MetadataQuery
from weaviate.collections.classes.config_named_vectors import _NamedVectorConfigCreate
from weaviate.collections.classes.config_vectorizers import VectorDistances
from weaviate.collections.classes.data import DataObject
from weaviate.collections.classes.filters import FilterValues, _Filters
from weaviate.collections.collection import CollectionAsync
from weaviate.exceptions import WeaviateClosedClientError, WeaviateConnectionError

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.data.vector import (
    DistanceFunction,
    GetFilteredRecordOptions,
    IndexKind,
    KernelSearchResults,
    SearchType,
    TModel,
    VectorSearch,
    VectorSearchOptions,
    VectorSearchResult,
    VectorStore,
    VectorStoreCollection,
    VectorStoreCollectionDefinition,
    VectorStoreField,
)
from semantic_kernel.exceptions import (
    ServiceInvalidExecutionSettingsError,
    VectorSearchExecutionException,
    VectorStoreException,
    VectorStoreInitializationException,
    VectorStoreModelValidationError,
    VectorStoreOperationException,
)
from semantic_kernel.kernel_pydantic import HttpsUrl, KernelBaseSettings
from semantic_kernel.kernel_types import OneOrMany
from semantic_kernel.utils.feature_stage_decorator import release_candidate

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover
if sys.version_info >= (3, 11):
    from typing import Self  # pragma: no cover
else:
    from typing_extensions import Self  # pragma: no cover

logger = logging.getLogger(__name__)

TKey = TypeVar("TKey", bound=str)

DISTANCE_FUNCTION_MAP: Final[dict[DistanceFunction, VectorDistances]] = {
    DistanceFunction.COSINE_DISTANCE: VectorDistances.COSINE,
    DistanceFunction.DOT_PROD: VectorDistances.DOT,
    DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE: VectorDistances.L2_SQUARED,
    DistanceFunction.MANHATTAN: VectorDistances.MANHATTAN,
    DistanceFunction.HAMMING: VectorDistances.HAMMING,
    DistanceFunction.DEFAULT: VectorDistances.COSINE,
}

INDEX_KIND_MAP: Final[dict[IndexKind, Callable]] = {
    IndexKind.HNSW: Configure.VectorIndex.hnsw,
    IndexKind.FLAT: Configure.VectorIndex.flat,
    IndexKind.DEFAULT: Configure.VectorIndex.flat,
}

DATATYPE_MAP: Final[dict[str, DataType]] = {
    "str": DataType.TEXT,
    "int": DataType.INT,
    "float": DataType.NUMBER,
    "bool": DataType.BOOL,
    "list[str]": DataType.TEXT_ARRAY,
    "list[int]": DataType.INT_ARRAY,
    "list[float]": DataType.NUMBER_ARRAY,
    "list[bool]": DataType.BOOL_ARRAY,
    "default": DataType.TEXT,
}


def _definition_to_weaviate_named_vectors(
    definition: VectorStoreCollectionDefinition,
) -> list[_NamedVectorConfigCreate]:
    """Convert vector store vector fields to Weaviate named vectors.

    Args:
        definition (VectorStoreRecordDefinition): The data model definition.

    Returns:
        list[_NamedVectorConfigCreate]: The Weaviate named vectors.
    """
    vector_list: list[_NamedVectorConfigCreate] = []

    for field in definition.vector_fields:
        if field.distance_function is None or field.distance_function not in DISTANCE_FUNCTION_MAP:
            raise VectorStoreModelValidationError(
                f"Distance function {field.distance_function} is not supported by Weaviate."
            )
        if field.index_kind is None or field.index_kind not in INDEX_KIND_MAP:
            raise VectorStoreModelValidationError(f"Index kind {field.index_kind} is not supported by Weaviate.")
        vector_list.append(
            Configure.NamedVectors.none(
                name=field.storage_name or field.name,  # type: ignore
                vector_index_config=INDEX_KIND_MAP[field.index_kind](
                    distance_metric=DISTANCE_FUNCTION_MAP[field.distance_function]
                ),
            )
        )
    return vector_list


@release_candidate
class WeaviateSettings(KernelBaseSettings):
    """Weaviate model settings.

    Args:
        url: HttpsUrl | None - Weaviate URL (Env var WEAVIATE_URL)
        api_key: SecretStr | None - Weaviate token (Env var WEAVIATE_API_KEY)
        local_host: str | None - Local Weaviate host, i.e. a Docker instance (Env var WEAVIATE_LOCAL_HOST)
        local_port: int | None - Local Weaviate port (Env var WEAVIATE_LOCAL_PORT)
        local_grpc_port: int | None - Local Weaviate gRPC port (Env var WEAVIATE_LOCAL_GRPC_PORT)
        use_embed: bool - Whether to use the embedded client
          (Env var WEAVIATE_USE_EMBED)
    """

    env_prefix: ClassVar[str] = "WEAVIATE_"

    # Using a Weaviate Cloud instance (WCD)
    url: HttpsUrl | None = None
    api_key: SecretStr | None = None

    # Using a local Weaviate instance (i.e. Weaviate in a Docker container)
    local_host: str | None = None
    local_port: int | None = None
    local_grpc_port: int | None = None

    # Using the client embedding options
    use_embed: bool = False

    @model_validator(mode="before")
    @classmethod
    def validate_settings(cls, data: Any) -> dict[str, Any]:
        """Validate Weaviate settings."""
        if isinstance(data, dict):
            enabled = sum([
                cls.is_using_weaviate_cloud(data),
                cls.is_using_local_weaviate(data),
                cls.is_using_client_embedding(data),
            ])

            if enabled == 0:
                raise ServiceInvalidExecutionSettingsError(
                    "Weaviate settings must specify either a ",
                    "Weaviate Cloud instance, a local Weaviate instance, or the client embedding options.",
                )
            if enabled > 1:
                raise ServiceInvalidExecutionSettingsError(
                    "Weaviate settings must specify only one of the following: ",
                    "Weaviate Cloud instance, a local Weaviate instance, or the client embedding options.",
                )

        return data

    @classmethod
    def is_using_weaviate_cloud(cls, data: dict[str, Any]) -> bool:
        """Return whether the Weaviate settings are using a Weaviate Cloud instance.

        `api_key` is not checked here. Clients should report an error if `api_key` is not set during initialization.
        """
        return data.get("url") is not None

    @classmethod
    def is_using_local_weaviate(cls, data: dict[str, Any]) -> bool:
        """Return whether the Weaviate settings are using a local Weaviate instance.

        `local_port` and `local_grpc_port` are not checked here.
        Clients should report an error if `local_port` and `local_grpc_port` are not set during initialization.
        """
        return data.get("local_host") is not None

    @classmethod
    def is_using_client_embedding(cls, data: dict[str, Any]) -> bool:
        """Return whether the Weaviate settings are using the client embedding options."""
        return data.get("use_embed") is True


@release_candidate
class WeaviateCollection(
    VectorStoreCollection[TKey, TModel],
    VectorSearch[TKey, TModel],
    Generic[TKey, TModel],
):
    """A Weaviate collection is a collection of records that are stored in a Weaviate database."""

    async_client: WeaviateAsyncClient
    named_vectors: bool = True
    supported_key_types: ClassVar[set[str] | None] = {"str"}
    supported_search_types: ClassVar[set[SearchType]] = {SearchType.VECTOR, SearchType.KEYWORD_HYBRID}

    def __init__(
        self,
        record_type: type[TModel],
        definition: VectorStoreCollectionDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        url: str | None = None,
        api_key: str | None = None,
        local_host: str | None = None,
        local_port: int | None = None,
        local_grpc_port: int | None = None,
        use_embed: bool = False,
        named_vectors: bool = True,
        async_client: WeaviateAsyncClient | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ):
        """Initialize a Weaviate collection.

        Args:
            record_type: The type of the data model.
            definition: The definition of the data model.
            collection_name: The name of the collection.
            embedding_generator: The embedding generator.
            url: The Weaviate URL
            api_key: The Weaviate API key.
            local_host: The local Weaviate host (i.e. Weaviate in a Docker container).
            local_port: The local Weaviate port.
            local_grpc_port: The local Weaviate gRPC port.
            use_embed: Whether to use the embedded client.
            named_vectors: Whether to use named vectors, or a single unnamed vector.
                In both cases the data model can be the same, but it has to have 1 vector
                field if named_vectors is False.
            async_client: A custom Weaviate async client.
            env_file_path: The path to the environment file.
            env_file_encoding: The encoding of the environment file.
        """
        managed_client: bool = False
        if not async_client:
            managed_client = True
            weaviate_settings = WeaviateSettings(
                url=url,
                api_key=api_key,
                local_host=local_host,
                local_port=local_port,
                local_grpc_port=local_grpc_port,
                use_embed=use_embed,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )

            try:
                if weaviate_settings.url:
                    async_client = use_async_with_weaviate_cloud(
                        cluster_url=str(weaviate_settings.url),
                        auth_credentials=Auth.api_key(weaviate_settings.api_key.get_secret_value())
                        if weaviate_settings.api_key
                        else None,
                    )
                elif weaviate_settings.local_host:
                    kwargs: dict[str, Any] = {
                        "host": weaviate_settings.local_host,
                        "port": weaviate_settings.local_port,
                        "grpc_port": weaviate_settings.local_grpc_port,
                    }
                    kwargs = {k: v for k, v in kwargs.items() if v is not None}
                    async_client = use_async_with_local(**kwargs)
                elif weaviate_settings.use_embed:
                    async_client = use_async_with_embedded()
                else:
                    raise NotImplementedError(
                        "Weaviate settings must specify either a custom client, a Weaviate Cloud instance,",
                        " a local Weaviate instance, or the client embedding options.",
                    )
            except Exception as e:
                raise VectorStoreInitializationException(f"Failed to initialize Weaviate client: {e}")

        super().__init__(
            record_type=record_type,
            definition=definition,
            collection_name=collection_name,
            async_client=async_client,  # type: ignore[call-arg]
            managed_client=managed_client,
            named_vectors=named_vectors,  # type: ignore[call-arg]
            embedding_generator=embedding_generator,
        )

    @field_validator("collection_name")
    @classmethod
    def collection_name_must_start_with_uppercase(cls, value: str) -> str:
        """By convention, the collection name starts with an uppercase letter.

        https://weaviate.io/developers/weaviate/manage-data/collections#create-a-collection
        Will change the collection name to start with an uppercase letter if it does not.
        """
        if value[0].isupper():
            return value
        return value[0].upper() + value[1:]

    @override
    async def _inner_upsert(
        self,
        records: Sequence[Any],
        **kwargs: Any,
    ) -> Sequence[TKey]:
        assert all([isinstance(record, DataObject) for record in records])  # nosec
        collection: CollectionAsync = self.async_client.collections.get(self.collection_name)
        response = await collection.data.insert_many(records)
        return [str(v) for _, v in response.uuids.items()]  # type: ignore[misc]

    @override
    async def _inner_get(
        self,
        keys: Sequence[TKey] | None = None,
        options: GetFilteredRecordOptions | None = None,
        **kwargs: Any,
    ) -> OneOrMany[Any] | None:
        if not keys:
            if options is not None:
                raise NotImplementedError("Get without keys is not yet implemented.")
            return None
        collection: CollectionAsync = self.async_client.collections.get(self.collection_name)
        result = await collection.query.fetch_objects(
            filters=Filter.any_of([Filter.by_id().equal(key) for key in keys]),
            include_vector=kwargs.get("include_vectors", False),
        )

        return result.objects

    @override
    async def _inner_delete(self, keys: Sequence[TKey], **kwargs: Any) -> None:
        collection: CollectionAsync = self.async_client.collections.get(self.collection_name)
        await collection.data.delete_many(where=Filter.any_of([Filter.by_id().equal(key) for key in keys]))

    @override
    async def _inner_search(
        self,
        search_type: SearchType,
        options: VectorSearchOptions,
        values: Any | None = None,
        vector: Sequence[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        collection: CollectionAsync = self.async_client.collections.get(self.collection_name)
        vector_field = self.definition.try_get_vector_field(options.vector_property_name)
        args = {
            "include_vector": options.include_vectors,
            "limit": options.top,
            "offset": options.skip,
            "return_metadata": MetadataQuery(distance=True),
            "target_vector": vector_field.storage_name or vector_field.name
            if self.named_vectors and vector_field
            else None,
        }
        if not vector:
            vector = await self._generate_vector_from_values(values, options)
        if not vector:
            raise VectorSearchExecutionException("No vector provided, or unable to generate a vector.")
        if filter := self._build_filter(options.filter):  # type: ignore
            args["filters"] = Filter.all_of(filter) if isinstance(filter, list) else filter
        if search_type == SearchType.VECTOR:
            if self.named_vectors and not vector_field:
                raise VectorSearchExecutionException(
                    "Vectorizable text search requires a vector field to be specified in the options."
                )
            try:
                results = await collection.query.near_vector(  # type: ignore
                    near_vector=vector,
                    **args,
                )
            except WeaviateClosedClientError as ex:
                raise VectorSearchExecutionException(
                    "Client is closed, please use the context manager or self.async_client.connect."
                ) from ex
            except Exception as ex:
                raise VectorSearchExecutionException(f"Failed searching using a vector: {ex}") from ex
            return KernelSearchResults(
                results=self._get_vector_search_results_from_results(results.objects), total_count=len(results.objects)
            )
        try:
            results = await collection.query.hybrid(  # type: ignore
                query=json.dumps(values) if isinstance(values, list) else values,
                vector=vector,
                **args,
            )
        except WeaviateClosedClientError as ex:
            raise VectorSearchExecutionException(
                "Client is closed, please use the context manager or self.async_client.connect."
            ) from ex
        except Exception as ex:
            raise VectorSearchExecutionException(f"Failed searching using hybrid: {ex}") from ex

        return KernelSearchResults(
            results=self._get_vector_search_results_from_results(results.objects), total_count=len(results.objects)
        )

    @override
    def _lambda_parser(self, node: ast.AST) -> "_Filters | FilterValues":
        # Use Weaviate Filter and operators for AST translation

        # Comparison operations
        match node:
            case ast.Compare():
                if len(node.ops) > 1:
                    # Chain comparisons (e.g., 1 < x < 3) become AND of each comparison
                    filters: list[_Filters] = []
                    for idx in range(len(node.ops)):
                        left = node.left if idx == 0 else node.comparators[idx - 1]
                        right: FilterValues = node.comparators[idx]  # type: ignore
                        op = node.ops[idx]
                        filters.append(self._lambda_parser(ast.Compare(left=left, ops=[op], comparators=[right])))  # type: ignore
                    return Filter.all_of(filters)
                left = self._lambda_parser(node.left)  # type: ignore
                right: FilterValues = self._lambda_parser(node.comparators[0])  # type: ignore
                op = node.ops[0]
                # left is property name, right is value
                if not isinstance(left, str):
                    raise NotImplementedError("Only simple property filters are supported.")
                match op:
                    case ast.Eq():
                        return Filter.by_property(left).equal(right)
                    case ast.NotEq():
                        return Filter.by_property(left).not_equal(right)
                    case ast.Gt():
                        return Filter.by_property(left).greater_than(right)
                    case ast.GtE():
                        return Filter.by_property(left).greater_or_equal(right)
                    case ast.Lt():
                        return Filter.by_property(left).less_than(right)
                    case ast.LtE():
                        return Filter.by_property(left).less_or_equal(right)
                    case ast.In():
                        return Filter.by_property(left).contains_any(right)  # type: ignore
                    case ast.NotIn():
                        # NotIn is not directly supported, so use NOT(contains_any)
                        raise NotImplementedError("NotIn is not directly supported.")
                raise NotImplementedError(f"Unsupported operator: {type(op)}")
            case ast.BoolOp():
                op = node.op  # type: ignore
                filters: list[_Filters] = [self._lambda_parser(v) for v in node.values]  # type: ignore
                if isinstance(op, ast.And):
                    return Filter.all_of(filters)
                if isinstance(op, ast.Or):
                    return Filter.any_of(filters)
                raise NotImplementedError(f"Unsupported BoolOp: {type(op)}")
            case ast.UnaryOp():
                raise NotImplementedError("Unary +, -, ~, ! are not supported in Weaviate filters.")
            case ast.Attribute():
                # Only allow attributes that are in the data model
                if node.attr not in self.definition.storage_names:
                    raise VectorStoreOperationException(
                        f"Field '{node.attr}' not in data model (storage property names are used)."
                    )
                return node.attr
            case ast.Name():
                # Only allow names that are in the data model
                if node.id not in self.definition.storage_names:
                    raise VectorStoreOperationException(
                        f"Field '{node.id}' not in data model (storage property names are used)."
                    )
                return node.id
            case ast.Constant():
                return node.value
        raise NotImplementedError(f"Unsupported AST node: {type(node)}")

    async def _inner_vectorized_search(
        self,
        collection: CollectionAsync,
        vector: list[float | int],
        vector_field: VectorStoreField | None,
        args: dict[str, Any],
    ) -> Any:
        if self.named_vectors and not vector_field:
            raise VectorSearchExecutionException(
                "Vectorizable text search requires a vector field to be specified in the options."
            )
        try:
            return await collection.query.near_vector(
                near_vector=vector,
                target_vector=vector_field.name if self.named_vectors and vector_field else None,
                return_metadata=MetadataQuery(distance=True),
                **args,
            )
        except WeaviateClosedClientError as ex:
            raise VectorSearchExecutionException(
                "Client is closed, please use the context manager or self.async_client.connect."
            ) from ex
        except Exception as ex:
            raise VectorSearchExecutionException(f"Failed searching using a vector: {ex}") from ex

    def _get_record_from_result(self, result: Any) -> Any:
        """Get the record from the returned search result."""
        return result

    def _get_score_from_result(self, result: Any) -> float | None:
        if result.metadata and result.metadata.score is not None:
            return result.metadata.score
        if result.metadata and result.metadata.distance is not None:
            return result.metadata.distance
        return None

    @override
    def _serialize_dicts_to_store_models(self, records: Sequence[dict[str, Any]], **kwargs: Any) -> Sequence[Any]:
        """Create a data object from a record based on the data model definition."""
        records_in_store_model: list[DataObject[dict[str, Any], None]] = []
        for record in records:
            properties = {field.storage_name or field.name: record[field.name] for field in self.definition.data_fields}
            # If key is None, Weaviate will generate a UUID
            key = record[self.definition.key_field.storage_name or self.definition.key_field.name]
            if self.named_vectors:
                vectors = {
                    vector.storage_name or vector.name: record[vector.name] for vector in self.definition.vector_fields
                }
            else:
                vectors = record[self.definition.vector_fields[0].storage_name or self.definition.vector_fields[0].name]
            records_in_store_model.append(DataObject(properties=properties, uuid=key, vector=vectors))
        return records_in_store_model

    @override
    def _deserialize_store_models_to_dicts(self, records: Sequence[Any], **kwargs: Any) -> Sequence[dict[str, Any]]:
        records_in_dict: list[dict[str, Any]] = []
        for record in records:
            properties = {
                field.name: record.properties[field.storage_name or field.name]
                for field in self.definition.data_fields
                if (field.storage_name or field.name) in record.properties
            }
            key = {self.definition.key_field.name: record.uuid}
            if not record.vector:
                records_in_dict.append(properties | key)
            else:
                if self.named_vectors:
                    vectors = {
                        vector.name: record.vector[vector.storage_name or vector.name]
                        for vector in self.definition.vector_fields
                        if (vector.storage_name or vector.name) in record.vector
                    }
                else:
                    vector_field = self.definition.vector_fields[0]
                    vectors = {vector_field.name: record.vector["default"]}
                records_in_dict.append(properties | key | vectors)
        return records_in_dict

    @override
    async def create_collection(self, **kwargs) -> None:
        """Create the collection in Weaviate.

        Args:
            **kwargs: Additional keyword arguments, when any kwargs are supplied they are passed
                straight to the Weaviate client.collections.create method.
                Make sure to check the arguments of that method for the specifications.
        """
        if not self.named_vectors and len(self.definition.vector_field_names) != 1:
            raise VectorStoreOperationException(
                "Named vectors must be enabled if there is not exactly one vector field in the data model definition."
            )
        if kwargs:
            try:
                await self.async_client.collections.create(**kwargs)
            except WeaviateClosedClientError as ex:
                raise VectorStoreOperationException(
                    "Client is closed, please use the context manager or self.async_client.connect."
                ) from ex
            except Exception as ex:
                raise VectorStoreOperationException(f"Failed to create collection: {ex}") from ex
        try:
            if self.named_vectors:
                vector_index_config = None
                vectorizer_config = _definition_to_weaviate_named_vectors(self.definition)
            else:
                vector_field = self.definition.vector_fields[0]
                if (
                    vector_field.distance_function is None
                    or vector_field.distance_function not in DISTANCE_FUNCTION_MAP
                ):
                    raise VectorStoreModelValidationError(
                        f"Distance function {vector_field.distance_function} is not supported by Weaviate."
                    )
                if vector_field.index_kind is None or vector_field.index_kind not in INDEX_KIND_MAP:
                    raise VectorStoreModelValidationError(
                        f"Index kind {vector_field.index_kind} is not supported by Weaviate."
                    )
                vector_index_config = INDEX_KIND_MAP[vector_field.index_kind](
                    distance_metric=DISTANCE_FUNCTION_MAP[vector_field.distance_function]
                )
                vectorizer_config = None

            properties: list[Property] = []
            for field in self.definition.data_fields:
                properties.append(
                    Property(
                        name=field.storage_name or field.name,
                        data_type=DATATYPE_MAP[field.type_ or "default"],
                        index_filterable=field.is_indexed,
                        index_full_text=field.is_full_text_indexed,
                    )
                )

            await self.async_client.collections.create(
                name=self.collection_name,
                properties=properties,
                vector_index_config=vector_index_config,
                vectorizer_config=vectorizer_config,
            )
        except WeaviateClosedClientError as ex:
            raise VectorStoreOperationException(
                "Client is closed, please use the context manager or self.async_client.connect."
            ) from ex
        except Exception as ex:
            raise VectorStoreOperationException(f"Failed to create collection: {ex}") from ex

    @override
    async def does_collection_exist(self, **kwargs) -> bool:
        """Check if the collection exists in Weaviate.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            bool: Whether the collection exists.
        """
        try:
            return await self.async_client.collections.exists(self.collection_name)
        except WeaviateClosedClientError as ex:
            raise VectorStoreOperationException(
                "Client is closed, please use the context manager or self.async_client.connect."
            ) from ex
        except Exception as ex:
            raise VectorStoreOperationException(f"Failed to check if collection exists: {ex}") from ex

    @override
    async def ensure_collection_deleted(self, **kwargs) -> None:
        """Delete the collection in Weaviate.

        Args:
            **kwargs: Additional keyword arguments.
        """
        try:
            await self.async_client.collections.delete(self.collection_name)
        except WeaviateClosedClientError as ex:
            raise VectorStoreOperationException(
                "Client is closed, please use the context manager or self.async_client.connect."
            ) from ex
        except Exception as ex:
            raise VectorStoreOperationException(f"Failed to delete collection: {ex}") from ex

    @override
    async def __aenter__(self) -> "WeaviateCollection":
        """Enter the context manager."""
        await self.async_client.connect()
        return self

    @override
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager."""
        if self.managed_client:
            await self.async_client.close()

    def _validate_data_model(self):
        super()._validate_data_model()
        if self.named_vectors and len(self.definition.vector_field_names) > 1:
            raise VectorStoreModelValidationError(
                "Named vectors must be enabled if there are more then 1 vector fields in the data model definition."
            )


@release_candidate
class WeaviateStore(VectorStore):
    """A Weaviate store is a vector store that uses Weaviate as the backend."""

    async_client: WeaviateAsyncClient

    def __init__(
        self,
        url: str | None = None,
        api_key: str | None = None,
        local_host: str | None = None,
        local_port: int | None = None,
        local_grpc_port: int | None = None,
        use_embed: bool = False,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        async_client: WeaviateAsyncClient | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ):
        """Initialize a Weaviate store.

        Args:
            url: The Weaviate URL.
            api_key: The Weaviate API key.
            local_host: The local Weaviate host (i.e. Weaviate in a Docker container).
            local_port: The local Weaviate port.
            local_grpc_port: The local Weaviate gRPC port.
            use_embed: Whether to use the embedded client.
            embedding_generator: The embedding generator.
            async_client: A custom Weaviate async client.
            env_file_path: The path to the environment file.
            env_file_encoding: The encoding of the environment file.
        """
        managed_client: bool = False
        if not async_client:
            managed_client = True
            weaviate_settings = WeaviateSettings(
                url=url,
                api_key=api_key,
                local_host=local_host,
                local_port=local_port,
                local_grpc_port=local_grpc_port,
                use_embed=use_embed,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )

            try:
                if weaviate_settings.url:
                    async_client = use_async_with_weaviate_cloud(
                        cluster_url=str(weaviate_settings.url),
                        auth_credentials=Auth.api_key(weaviate_settings.api_key.get_secret_value())
                        if weaviate_settings.api_key
                        else None,
                    )
                elif weaviate_settings.local_host:
                    kwargs: dict[str, Any] = {
                        "host": weaviate_settings.local_host,
                        "port": weaviate_settings.local_port,
                        "grpc_port": weaviate_settings.local_grpc_port,
                    }
                    kwargs = {k: v for k, v in kwargs.items() if v is not None}
                    async_client = use_async_with_local(
                        **kwargs,
                    )
                elif weaviate_settings.use_embed:
                    async_client = use_async_with_embedded()
                else:
                    raise NotImplementedError(
                        "Weaviate settings must specify either a custom client, a Weaviate Cloud instance,",
                        " a local Weaviate instance, or the client embedding options.",
                    )
            except Exception as e:
                raise VectorStoreInitializationException(f"Failed to initialize Weaviate client: {e}")

        super().__init__(
            async_client=async_client, managed_client=managed_client, embedding_generator=embedding_generator
        )

    @override
    def get_collection(
        self,
        record_type: type[TModel],
        *,
        definition: VectorStoreCollectionDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        **kwargs: Any,
    ) -> WeaviateCollection:
        return WeaviateCollection(
            record_type=record_type,
            definition=definition,
            collection_name=collection_name,
            embedding_generator=embedding_generator or self.embedding_generator,
            async_client=self.async_client,
            **kwargs,
        )

    @override
    async def list_collection_names(self, **kwargs) -> Sequence[str]:
        async with self.async_client:
            try:
                collections = await self.async_client.collections.list_all()
                return [collection.name for collection in collections.values()]
            except Exception as e:
                raise VectorStoreOperationException(f"Failed to list Weaviate collections: {e}")

    @override
    async def __aenter__(self) -> Self:
        """Enter the context manager."""
        if not self.async_client.is_connected():
            try:
                await self.async_client.connect()
            except WeaviateConnectionError as exc:
                raise VectorStoreException("Weaviate client cannot connect.") from exc
        return self

    @override
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager."""
        if self.managed_client:
            await self.async_client.close()
