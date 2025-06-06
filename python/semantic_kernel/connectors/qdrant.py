# Copyright (c) Microsoft. All rights reserved.

import ast
import logging
import sys
from collections.abc import MutableMapping, Sequence
from copy import deepcopy
from typing import Any, ClassVar, Final, Generic, TypeVar

from pydantic import HttpUrl, SecretStr, ValidationError, model_validator
from qdrant_client.async_qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Datatype,
    Distance,
    FieldCondition,
    Filter,
    Fusion,
    FusionQuery,
    MatchAny,
    MatchValue,
    PointStruct,
    Prefetch,
    QueryResponse,
    Range,
    ScoredPoint,
    VectorParams,
)
from typing_extensions import override

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
)
from semantic_kernel.exceptions import (
    VectorSearchExecutionException,
    VectorStoreInitializationException,
    VectorStoreModelValidationError,
    VectorStoreOperationException,
)
from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.kernel_types import OneOrMany
from semantic_kernel.utils.feature_stage_decorator import release_candidate
from semantic_kernel.utils.telemetry.user_agent import APP_INFO, prepend_semantic_kernel_to_user_agent

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

logger: logging.Logger = logging.getLogger(__name__)
TKey = TypeVar("TKey", bound=str | int)

DISTANCE_FUNCTION_MAP: Final[dict[DistanceFunction, Distance]] = {
    DistanceFunction.COSINE_SIMILARITY: Distance.COSINE,
    DistanceFunction.DOT_PROD: Distance.DOT,
    DistanceFunction.EUCLIDEAN_DISTANCE: Distance.EUCLID,
    DistanceFunction.MANHATTAN: Distance.MANHATTAN,
    DistanceFunction.DEFAULT: Distance.COSINE,
}
INDEX_KIND_MAP: Final[dict[IndexKind, str]] = {
    IndexKind.HNSW: "hnsw",
    IndexKind.DEFAULT: "hnsw",
}
TYPE_MAPPER_VECTOR: Final[dict[str, Datatype]] = {
    "float": Datatype.FLOAT32,
    "int": Datatype.UINT8,
    "binary": Datatype.UINT8,
    "default": Datatype.FLOAT32,
}
IN_MEMORY_STRING: Final[str] = ":memory:"


@release_candidate
class QdrantSettings(KernelBaseSettings):
    """Qdrant settings currently used by the Qdrant Vector Record Store."""

    env_prefix: ClassVar[str] = "QDRANT_"

    url: HttpUrl | None = None
    api_key: SecretStr | None = None
    host: str | None = None
    port: int | None = None
    grpc_port: int | None = None
    path: str | None = None
    location: str | None = None
    prefer_grpc: bool = False

    @model_validator(mode="before")
    def validate_settings(cls, values: dict):
        """Validate the settings."""
        if (
            isinstance(values, dict)
            and "url" not in values
            and "host" not in values
            and "path" not in values
            and "location" not in values
        ):
            values["location"] = IN_MEMORY_STRING
        return values

    def model_dump(self, **kwargs):
        """Dump the model."""
        dump = super().model_dump(**kwargs)
        if "api_key" in dump:
            dump["api_key"] = dump["api_key"].get_secret_value()
        if "url" in dump:
            dump["url"] = str(dump["url"])
        return dump


@release_candidate
class QdrantCollection(
    VectorStoreCollection[TKey, TModel],
    VectorSearch[TKey, TModel],
    Generic[TKey, TModel],
):
    """A QdrantCollection is a memory collection that uses Qdrant as the backend."""

    qdrant_client: AsyncQdrantClient
    named_vectors: bool
    supported_key_types: ClassVar[set[str] | None] = {"str", "int"}
    supported_vector_types: ClassVar[set[str] | None] = {"float", "int"}
    supported_search_types: ClassVar[set[SearchType]] = {SearchType.VECTOR, SearchType.KEYWORD_HYBRID}

    def __init__(
        self,
        record_type: type[TModel],
        definition: VectorStoreCollectionDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        named_vectors: bool = True,
        url: str | None = None,
        api_key: str | None = None,
        host: str | None = None,
        port: int | None = None,
        grpc_port: int | None = None,
        path: str | None = None,
        location: str | None = None,
        prefer_grpc: bool | None = None,
        client: AsyncQdrantClient | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initializes a new instance of the QdrantVectorRecordStore.

        When using qdrant client, make sure to supply url and api_key.
        When using qdrant server, make sure to supply url or host and optionally port.
        When using qdrant local, either supply path to use a persisted qdrant instance
            or set location to ":memory:" to use an in-memory qdrant instance.
        When nothing is supplied, it defaults to an in-memory qdrant instance.
        You can also supply a async qdrant client directly.

        Args:
            record_type (type[TModel]): The type of the data model.
            definition (VectorStoreRecordDefinition): The model fields, optional.
            collection_name (str): The name of the collection, optional.
            embedding_generator (EmbeddingGeneratorBase): The embedding generator to use, optional.
            named_vectors (bool): If true, vectors are stored with name (default: True).
            url (str): The URL of the Qdrant server (default: {None}).
            api_key (str): The API key for the Qdrant server (default: {None}).
            host (str): The host of the Qdrant server (default: {None}).
            port (int): The port of the Qdrant server (default: {None}).
            grpc_port (int): The gRPC port of the Qdrant server (default: {None}).
            path (str): The path of the Qdrant server (default: {None}).
            location (str): The location of the Qdrant server (default: {None}).
            prefer_grpc (bool): If true, gRPC will be preferred (default: {None}).
            client (AsyncQdrantClient): The Qdrant client to use (default: {None}).
            env_file_path (str): Use the environment settings file as a fallback to environment variables.
            env_file_encoding (str): The encoding of the environment settings file.
            **kwargs: Additional keyword arguments passed to the client constructor.

        """
        if client:
            super().__init__(
                record_type=record_type,
                definition=definition,
                collection_name=collection_name,
                qdrant_client=client,  # type: ignore
                named_vectors=named_vectors,  # type: ignore
                managed_client=False,
                embedding_generator=embedding_generator,
            )
            return

        try:
            settings = QdrantSettings(
                url=url,
                api_key=api_key,
                host=host,
                port=port,
                grpc_port=grpc_port,
                path=path,
                location=location,
                prefer_grpc=prefer_grpc,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise VectorStoreInitializationException("Failed to create Qdrant settings.", ex) from ex
        if APP_INFO:
            kwargs.setdefault("metadata", {})
            kwargs["metadata"] = prepend_semantic_kernel_to_user_agent(kwargs["metadata"])
        try:
            client = AsyncQdrantClient(**settings.model_dump(exclude_none=True), **kwargs)
        except ValueError as ex:
            raise VectorStoreInitializationException("Failed to create Qdrant client.", ex) from ex
        super().__init__(
            record_type=record_type,
            definition=definition,
            collection_name=collection_name,
            qdrant_client=client,
            named_vectors=named_vectors,
            embedding_generator=embedding_generator,
        )

    @override
    async def _inner_upsert(
        self,
        records: Sequence[PointStruct],
        **kwargs: Any,
    ) -> Sequence[TKey]:
        await self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=records,
            **kwargs,
        )
        return [record.id for record in records]  # type: ignore

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
        if "with_vectors" not in kwargs:
            kwargs["with_vectors"] = kwargs.pop("include_vectors", True)
        return await self.qdrant_client.retrieve(
            collection_name=self.collection_name,
            ids=keys,
            **kwargs,
        )

    @override
    async def _inner_delete(self, keys: Sequence[TKey], **kwargs: Any) -> None:
        await self.qdrant_client.delete(
            collection_name=self.collection_name,
            points_selector=keys,
            **kwargs,
        )

    @override
    async def _inner_search(
        self,
        search_type: SearchType,
        options: VectorSearchOptions,
        values: Any | None = None,
        vector: Sequence[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        query_vector: tuple[str, Sequence[float | int]] | Sequence[float | int] | None = None

        if not vector:
            vector = await self._generate_vector_from_values(values, options)

        if not vector:
            raise VectorSearchExecutionException("Search requires a vector.")

        vector_field = self.definition.try_get_vector_field(options.vector_property_name)
        if not vector_field:
            raise VectorStoreOperationException(
                f"Vector field {options.vector_property_name} not found in data model definition."
            )
        query_vector = (vector_field.storage_name or vector_field.name, vector) if self.named_vectors else vector
        filters: Filter | list[Filter] | None = self._build_filter(options.filter)  # type: ignore
        filter: Filter | None = Filter(must=filters) if filters and isinstance(filters, list) else filters  # type: ignore
        if search_type == SearchType.VECTOR:
            results = await self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,  # type: ignore
                query_filter=filter,
                with_vectors=options.include_vectors,
                limit=options.top,
                offset=options.skip,
                **kwargs,
            )
        else:
            # Hybrid search: vector + keywords (RRF fusion)
            # 1. Get keywords and text field
            if not values:
                raise VectorSearchExecutionException("Hybrid search requires non-empty keywords in values.")
            if not options.additional_property_name:
                raise VectorSearchExecutionException("Hybrid search requires a keyword field name.")
            text_field = next(
                field
                for field in self.definition.fields
                if field.name == options.additional_property_name
                or field.storage_name == options.additional_property_name
            )
            if not text_field:
                raise VectorStoreOperationException(
                    f"Keyword field {options.additional_property_name} not found in data model definition."
                )
            keyword_filter = deepcopy(filter) if filter else Filter()
            keyword_sub_filter = Filter(
                should=[
                    FieldCondition(key=text_field.storage_name or text_field.name, match=MatchAny(any=[kw]))
                    for kw in values
                ]
            )
            if isinstance(keyword_filter.must, list):
                keyword_filter.must.append(keyword_sub_filter)
            elif isinstance(keyword_filter.must, Filter):
                keyword_filter.must = Filter(must=[keyword_filter.must, keyword_sub_filter])
            else:
                keyword_filter.must = keyword_sub_filter

            points = await self.qdrant_client.query_points(
                collection_name=self.collection_name,
                prefetch=[
                    Prefetch(
                        query=vector,  # type: ignore
                        using=vector_field.storage_name or vector_field.name,
                        filter=filter,
                        limit=options.top,
                    ),
                    Prefetch(filter=keyword_filter),
                ],
                query=FusionQuery(fusion=Fusion.RRF),
                limit=options.top,
                offset=options.skip,
                with_vectors=options.include_vectors,
                **kwargs,
            )
            results = points.points

        return KernelSearchResults(
            results=self._get_vector_search_results_from_results(results, options),
            total_count=len(results) if options.include_total_count else None,
        )

    @override
    def _get_record_from_result(self, result: ScoredPoint | QueryResponse) -> Any:
        return result

    @override
    def _get_score_from_result(self, result: ScoredPoint) -> float:
        return result.score

    @override
    def _lambda_parser(self, node: ast.AST) -> Any:
        # Qdrant filter translation: output a qdrant_client.models.Filter or FieldCondition tree
        # Use correct Match subtypes: MatchAny, MatchValue, etc.
        # See: https://python-client.qdrant.tech/qdrant_client.http.models.models#qdrant_client.http.models.models.Filter
        match node:
            case ast.Compare():
                if len(node.ops) > 1:
                    # Chain comparisons (e.g., 1 < x < 3) become AND of each comparison
                    conditions = []
                    for idx in range(len(node.ops)):
                        left = node.left if idx == 0 else node.comparators[idx - 1]
                        right = node.comparators[idx]
                        op = node.ops[idx]
                        conditions.append(self._lambda_parser(ast.Compare(left=left, ops=[op], comparators=[right])))
                    return Filter(must=conditions)
                left = self._lambda_parser(node.left)
                right = self._lambda_parser(node.comparators[0])
                op = node.ops[0]
                match op:
                    case ast.In():
                        # IN: left in right (right is a list)
                        return FieldCondition(key=left, match=MatchAny(any=right))
                    case ast.NotIn():
                        # NOT IN: left not in right
                        return Filter(must_not=[FieldCondition(key=left, match=MatchAny(any=right))])
                    case ast.Eq():
                        return FieldCondition(key=left, match=MatchValue(value=right))
                    case ast.NotEq():
                        return Filter(must_not=[FieldCondition(key=left, match=MatchValue(value=right))])
                    case ast.Gt():
                        return FieldCondition(key=left, range=Range(gt=right))
                    case ast.GtE():
                        return FieldCondition(key=left, range=Range(gte=right))
                    case ast.Lt():
                        return FieldCondition(key=left, range=Range(lt=right))
                    case ast.LtE():
                        return FieldCondition(key=left, range=Range(lte=right))
                raise NotImplementedError(f"Unsupported operator: {type(op)}")
            case ast.BoolOp():
                op = node.op  # type: ignore
                values = [self._lambda_parser(v) for v in node.values]
                if isinstance(op, ast.And):
                    return Filter(must=values)
                if isinstance(op, ast.Or):
                    return Filter(should=values)
                raise NotImplementedError(f"Unsupported BoolOp: {type(op)}")
            case ast.UnaryOp():
                match node.op:
                    case ast.Not():
                        operand = self._lambda_parser(node.operand)
                        return Filter(must_not=[operand])
                    case ast.UAdd() | ast.USub() | ast.Invert():
                        raise NotImplementedError("Unary +, -, ~ are not supported in Qdrant filters.")
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
            case ast.List():
                return [self._lambda_parser(elt) for elt in node.elts]
        raise NotImplementedError(f"Unsupported AST node: {type(node)}")

    @override
    def _serialize_dicts_to_store_models(
        self,
        records: Sequence[dict[str, Any]],
        **kwargs: Any,
    ) -> Sequence[PointStruct]:
        return [
            PointStruct(
                id=record.pop(self._key_field_name),
                vector=record.pop(self.definition.vector_field_names[0])
                if not self.named_vectors
                else {
                    field.storage_name or field.name: record.pop(field.name) for field in self.definition.vector_fields
                },
                payload=record,
            )
            for record in records
        ]

    @override
    def _deserialize_store_models_to_dicts(
        self,
        records: Sequence[PointStruct] | Sequence[ScoredPoint],
        **kwargs: Any,
    ) -> Sequence[dict[str, Any]]:
        return [
            {
                self._key_field_name: record.id,
                **(record.payload if record.payload else {}),
                **(
                    {}
                    if not record.vector
                    else record.vector
                    if isinstance(record.vector, dict)
                    else {self.definition.vector_field_names[0]: record.vector}
                ),
            }
            for record in records
        ]

    @override
    async def create_collection(self, **kwargs) -> None:
        """Create a new collection in Qdrant.

        Args:
            **kwargs: Additional keyword arguments.
                You can supply all keyword arguments supported by the QdrantClient.create_collection method.
                This method creates the vectors_config automatically when not supplied, other params are not set.
                Collection name will be set to the collection_name property, cannot be overridden.
        """
        if "vectors_config" not in kwargs:
            if self.named_vectors:
                vectors_config: MutableMapping[str, VectorParams] = {}
                for field in self.definition.vector_fields:
                    if field.index_kind not in INDEX_KIND_MAP:
                        raise VectorStoreOperationException(f"Index kind {field.index_kind} is not supported.")
                    if field.distance_function not in DISTANCE_FUNCTION_MAP:
                        raise VectorStoreOperationException(
                            f"Distance function {field.distance_function} is not supported."
                        )
                    vectors_config[field.storage_name or field.name] = VectorParams(
                        size=field.dimensions,
                        distance=DISTANCE_FUNCTION_MAP[field.distance_function],
                        datatype=TYPE_MAPPER_VECTOR[field.type_ or "default"],
                    )
                kwargs["vectors_config"] = vectors_config
            else:
                vector = self.definition.try_get_vector_field(None)
                if not vector:
                    raise VectorStoreOperationException("Vector field not found in data model definition.")
                if vector.distance_function not in DISTANCE_FUNCTION_MAP:
                    raise VectorStoreOperationException(
                        f"Distance function {vector.distance_function} is not supported."
                    )
                kwargs["vectors_config"] = VectorParams(
                    size=vector.dimensions,
                    distance=DISTANCE_FUNCTION_MAP[vector.distance_function],
                    datatype=TYPE_MAPPER_VECTOR[vector.type_ or "default"],
                )
        if "collection_name" not in kwargs:
            kwargs["collection_name"] = self.collection_name
        await self.qdrant_client.create_collection(**kwargs)

    @override
    async def does_collection_exist(self, **kwargs) -> bool:
        return await self.qdrant_client.collection_exists(self.collection_name, **kwargs)

    @override
    async def ensure_collection_deleted(self, **kwargs) -> None:
        await self.qdrant_client.delete_collection(self.collection_name, **kwargs)

    def _validate_data_model(self):
        """Internal function that should be overloaded by child classes to validate datatypes, etc.

        This should take the VectorStoreRecordDefinition from the item_type and validate it against the store.

        Checks should include, allowed naming of parameters, allowed data types, allowed vector dimensions.
        """
        super()._validate_data_model()
        if len(self.definition.vector_field_names) > 1 and not self.named_vectors:
            raise VectorStoreModelValidationError("Only one vector field is allowed when not using named vectors.")

    @override
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager."""
        if self.managed_client:
            await self.qdrant_client.close()


@release_candidate
class QdrantStore(VectorStore):
    """A QdrantStore is a memory store that uses Qdrant as the backend."""

    qdrant_client: AsyncQdrantClient

    def __init__(
        self,
        url: str | None = None,
        api_key: str | None = None,
        host: str | None = None,
        port: int | None = None,
        grpc_port: int | None = None,
        path: str | None = None,
        location: str | None = None,
        prefer_grpc: bool | None = None,
        client: AsyncQdrantClient | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initializes a new instance of the QdrantVectorRecordStore.

        When using qdrant client, make sure to supply url and api_key.
        When using qdrant server, make sure to supply url or host and optionally port.
        When using qdrant local, either supply path to use a persisted qdrant instance
            or set location to ":memory:" to use an in-memory qdrant instance.
        When nothing is supplied, it defaults to an in-memory qdrant instance.
        You can also supply a async qdrant client directly.

        Args:
            url: The URL of the Qdrant server (default: {None}).
            api_key: The API key for the Qdrant server (default: {None}).
            host: The host of the Qdrant server (default: {None}).
            port: The port of the Qdrant server (default: {None}).
            grpc_port: The gRPC port of the Qdrant server (default: {None}).
            path: The path of the Qdrant server (default: {None}).
            location: The location of the Qdrant server (default: {None}).
            prefer_grpc: If true, gRPC will be preferred (default: {None}).
            client: The Qdrant client to use (default: {None}).
            embedding_generator: The embedding generator to use (default: {None}).
            env_file_path: Use the environment settings file as a fallback to environment variables.
            env_file_encoding: The encoding of the environment settings file.
            **kwargs: Additional keyword arguments passed to the client constructor.

        """
        if client:
            super().__init__(
                qdrant_client=client, managed_client=False, embedding_generator=embedding_generator, **kwargs
            )
            return

        try:
            settings = QdrantSettings(
                url=url,
                api_key=api_key,
                host=host,
                port=port,
                grpc_port=grpc_port,
                path=path,
                location=location,
                prefer_grpc=prefer_grpc,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise VectorStoreInitializationException("Failed to create Qdrant settings.", ex) from ex
        if APP_INFO:
            kwargs.setdefault("metadata", {})
            kwargs["metadata"] = prepend_semantic_kernel_to_user_agent(kwargs["metadata"])
        try:
            client = AsyncQdrantClient(**settings.model_dump(exclude_none=True), **kwargs)
        except ValueError as ex:
            raise VectorStoreInitializationException("Failed to create Qdrant client.", ex) from ex
        super().__init__(qdrant_client=client, embedding_generator=embedding_generator, **kwargs)

    @override
    def get_collection(
        self,
        record_type: type[TModel],
        *,
        definition: VectorStoreCollectionDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        **kwargs: Any,
    ) -> QdrantCollection:
        return QdrantCollection(
            record_type=record_type,
            definition=definition,
            collection_name=collection_name,
            client=self.qdrant_client,
            embedding_generator=embedding_generator or self.embedding_generator,
            **kwargs,
        )

    @override
    async def list_collection_names(self, **kwargs: Any) -> Sequence[str]:
        collections = await self.qdrant_client.get_collections()
        return [collection.name for collection in collections.collections]

    @override
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        if self.managed_client:
            await self.qdrant_client.close()
