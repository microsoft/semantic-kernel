# Copyright (c) Microsoft. All rights reserved.

import ast
import asyncio
import logging
import sys
from collections.abc import Sequence
from typing import Any, ClassVar, Final, Generic, TypeVar

from pydantic import SecretStr, ValidationError
from pymilvus import DataType, MilvusClient

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

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

logger: logging.Logger = logging.getLogger(__name__)
TKey = TypeVar("TKey", bound=str | int)

DEFAULT_URI: Final[str] = "http://localhost:19530"
DEFAULT_VARCHAR_LENGTH: Final[int] = 65535

# Milvus metric types, see https://milvus.io/docs/metric.md
DISTANCE_FUNCTION_MAP: Final[dict[DistanceFunction, str]] = {
    DistanceFunction.COSINE_SIMILARITY: "COSINE",
    DistanceFunction.COSINE_DISTANCE: "COSINE",
    DistanceFunction.DOT_PROD: "IP",
    DistanceFunction.EUCLIDEAN_DISTANCE: "L2",
    DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE: "L2",
    DistanceFunction.HAMMING: "HAMMING",
    DistanceFunction.DEFAULT: "COSINE",
}
# Milvus index types, see https://milvus.io/docs/index.md
INDEX_KIND_MAP: Final[dict[IndexKind, str]] = {
    IndexKind.HNSW: "HNSW",
    IndexKind.FLAT: "FLAT",
    IndexKind.IVF_FLAT: "IVF_FLAT",
    IndexKind.DISK_ANN: "DISKANN",
    IndexKind.DEFAULT: "AUTOINDEX",
}
# Mapping of the data model type strings to the Milvus scalar DataType.
# Unmapped or unknown types fall back to VARCHAR, extra fields are stored via the dynamic field.
TYPE_MAP_SCALAR: Final[dict[str, DataType]] = {
    "str": DataType.VARCHAR,
    "int": DataType.INT64,
    "float": DataType.DOUBLE,
    "bool": DataType.BOOL,
    "dict": DataType.JSON,
    "list": DataType.JSON,
    "default": DataType.VARCHAR,
}


@release_candidate
class MilvusSettings(KernelBaseSettings):
    """Milvus settings used by the Milvus vector store connectors.

    The settings are first loaded from keyword arguments and then from environment
    variables (prefixed with ``MILVUS_``) and finally from an optional env file.
    """

    env_prefix: ClassVar[str] = "MILVUS_"

    uri: str | None = None
    token: SecretStr | None = None
    user: str | None = None
    password: SecretStr | None = None
    db_name: str | None = None


def _build_client_kwargs(settings: MilvusSettings) -> dict[str, Any]:
    """Build the keyword arguments for the MilvusClient from the settings."""
    client_kwargs: dict[str, Any] = {"uri": settings.uri or DEFAULT_URI}
    if settings.token:
        client_kwargs["token"] = settings.token.get_secret_value()
    if settings.user:
        client_kwargs["user"] = settings.user
    if settings.password:
        client_kwargs["password"] = settings.password.get_secret_value()
    if settings.db_name:
        client_kwargs["db_name"] = settings.db_name
    return client_kwargs


@release_candidate
class MilvusCollection(
    VectorStoreCollection[TKey, TModel],
    VectorSearch[TKey, TModel],
    Generic[TKey, TModel],
):
    """A MilvusCollection is a vector store collection that uses Milvus as the backend."""

    milvus_client: MilvusClient
    supported_key_types: ClassVar[set[str] | None] = {"str", "int"}
    supported_vector_types: ClassVar[set[str] | None] = {"float"}
    supported_search_types: ClassVar[set[SearchType]] = {SearchType.VECTOR}

    def __init__(
        self,
        record_type: type[TModel],
        definition: VectorStoreCollectionDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        uri: str | None = None,
        token: str | None = None,
        user: str | None = None,
        password: str | None = None,
        db_name: str | None = None,
        client: MilvusClient | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a new instance of the MilvusCollection.

        Supply either a pre-built ``client`` or the connection parameters. When nothing is
        supplied the collection connects to a local Milvus server at ``http://localhost:19530``.
        A local ``.db`` path can be passed as ``uri`` to use Milvus Lite.

        Args:
            record_type: The type of the data model.
            definition: The model fields, optional.
            collection_name: The name of the collection, optional.
            embedding_generator: The embedding generator to use, optional.
            uri: The URI of the Milvus server or a local Milvus Lite ``.db`` path.
            token: The token (or ``user:password``) used to authenticate.
            user: The username used to authenticate.
            password: The password used to authenticate.
            db_name: The Milvus database to use.
            client: A pre-built MilvusClient to use, if supplied the other connection
                parameters are ignored and the client is not closed by this collection.
            env_file_path: Use the environment settings file as a fallback to environment variables.
            env_file_encoding: The encoding of the environment settings file.
            **kwargs: Additional keyword arguments passed to the MilvusClient constructor.
        """
        if client:
            super().__init__(
                record_type=record_type,
                definition=definition,
                collection_name=collection_name,
                milvus_client=client,  # type: ignore[call-arg]
                managed_client=False,
                embedding_generator=embedding_generator,
            )
            return

        try:
            settings = MilvusSettings(
                uri=uri,
                token=token,
                user=user,
                password=password,
                db_name=db_name,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise VectorStoreInitializationException("Failed to create Milvus settings.", ex) from ex
        try:
            client = MilvusClient(**_build_client_kwargs(settings), **kwargs)
        except Exception as ex:
            raise VectorStoreInitializationException("Failed to create Milvus client.", ex) from ex
        super().__init__(
            record_type=record_type,
            definition=definition,
            collection_name=collection_name,
            milvus_client=client,  # type: ignore[call-arg]
            embedding_generator=embedding_generator,
        )

    @property
    def _key_storage_name(self) -> str:
        key_field = self.definition.key_field
        return key_field.storage_name or key_field.name

    @override
    async def _inner_upsert(
        self,
        records: Sequence[dict[str, Any]],
        **kwargs: Any,
    ) -> Sequence[TKey]:
        await asyncio.to_thread(
            self.milvus_client.upsert,
            collection_name=self.collection_name,
            data=list(records),
            **kwargs,
        )
        return [record[self._key_storage_name] for record in records]

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
        return await asyncio.to_thread(
            self.milvus_client.get,
            collection_name=self.collection_name,
            ids=list(keys),
            output_fields=["*"],
            **kwargs,
        )

    @override
    async def _inner_delete(self, keys: Sequence[TKey], **kwargs: Any) -> None:
        await asyncio.to_thread(
            self.milvus_client.delete,
            collection_name=self.collection_name,
            ids=list(keys),
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
        if not vector:
            vector = await self._generate_vector_from_values(values, options)
        if not vector:
            raise VectorSearchExecutionException("Search requires a vector.")

        vector_field = self.definition.try_get_vector_field(options.vector_property_name)
        if not vector_field:
            raise VectorStoreOperationException(
                f"Vector field '{options.vector_property_name}' not found in the data model definition."
            )
        if vector_field.distance_function not in DISTANCE_FUNCTION_MAP:
            raise VectorStoreOperationException(
                f"Distance function '{vector_field.distance_function}' is not supported by Milvus."
            )

        filter_expression = ""
        if filters := self._build_filter(options.filter):
            filter_expression = filters if isinstance(filters, str) else " and ".join(filters)

        search_params: dict[str, Any] = {"metric_type": DISTANCE_FUNCTION_MAP[vector_field.distance_function]}
        if options.skip:
            search_params["offset"] = options.skip

        results = await asyncio.to_thread(
            self.milvus_client.search,
            collection_name=self.collection_name,
            data=[list(vector)],
            anns_field=vector_field.storage_name or vector_field.name,
            limit=options.top,
            filter=filter_expression,
            output_fields=self.definition.get_storage_names(include_vector_fields=options.include_vectors),
            search_params=search_params,
            **kwargs,
        )
        # Milvus returns one list of hits per query vector, we only send one vector.
        hits = list(results[0]) if results else []
        return KernelSearchResults(
            results=self._get_vector_search_results_from_results(hits, options),
            total_count=len(hits) if options.include_total_count else None,
        )

    @override
    def _get_record_from_result(self, result: dict[str, Any]) -> Any:
        record = dict(result.get("entity") or {})
        if "id" in result:
            record.setdefault(self._key_storage_name, result["id"])
        return record

    @override
    def _get_score_from_result(self, result: dict[str, Any]) -> float | None:
        return result.get("distance")

    @override
    def _serialize_dicts_to_store_models(
        self,
        records: Sequence[dict[str, Any]],
        **kwargs: Any,
    ) -> Sequence[dict[str, Any]]:
        store_models: list[dict[str, Any]] = []
        for record in records:
            model: dict[str, Any] = {}
            consumed: set[str] = set()
            for field in self.definition.fields:
                if field.name in record:
                    model[field.storage_name or field.name] = record[field.name]
                    consumed.add(field.name)
            # Pass extra (dynamic) fields through unchanged.
            for key, value in record.items():
                if key not in consumed:
                    model[key] = value
            store_models.append(model)
        return store_models

    @override
    def _deserialize_store_models_to_dicts(
        self,
        records: Sequence[dict[str, Any]],
        **kwargs: Any,
    ) -> Sequence[dict[str, Any]]:
        known_storage_names = {field.storage_name or field.name for field in self.definition.fields}
        dicts: list[dict[str, Any]] = []
        for record in records:
            item: dict[str, Any] = {}
            for field in self.definition.fields:
                storage_name = field.storage_name or field.name
                if storage_name in record:
                    item[field.name] = record[storage_name]
            # Pass extra (dynamic) fields through unchanged.
            for key, value in record.items():
                if key not in known_storage_names:
                    item[key] = value
            dicts.append(item)
        return dicts

    def _build_schema_and_index(self) -> tuple[Any, Any]:
        """Build the Milvus collection schema and index parameters from the data model definition."""
        schema = MilvusClient.create_schema(auto_id=False, enable_dynamic_field=True)
        key_field = self.definition.key_field
        if key_field.type_ == "int":
            schema.add_field(
                field_name=key_field.storage_name or key_field.name,
                datatype=DataType.INT64,
                is_primary=True,
            )
        else:
            schema.add_field(
                field_name=key_field.storage_name or key_field.name,
                datatype=DataType.VARCHAR,
                is_primary=True,
                max_length=DEFAULT_VARCHAR_LENGTH,
            )
        for field in self.definition.data_fields:
            datatype = TYPE_MAP_SCALAR.get(field.type_ or "default", TYPE_MAP_SCALAR["default"])
            if datatype == DataType.VARCHAR:
                schema.add_field(
                    field_name=field.storage_name or field.name,
                    datatype=datatype,
                    max_length=DEFAULT_VARCHAR_LENGTH,
                )
            else:
                schema.add_field(field_name=field.storage_name or field.name, datatype=datatype)

        index_params = self.milvus_client.prepare_index_params()
        for field in self.definition.vector_fields:
            if field.index_kind not in INDEX_KIND_MAP:
                raise VectorStoreOperationException(f"Index kind '{field.index_kind}' is not supported by Milvus.")
            if field.distance_function not in DISTANCE_FUNCTION_MAP:
                raise VectorStoreOperationException(
                    f"Distance function '{field.distance_function}' is not supported by Milvus."
                )
            schema.add_field(
                field_name=field.storage_name or field.name,
                datatype=DataType.FLOAT_VECTOR,
                dim=field.dimensions,
            )
            index_params.add_index(
                field_name=field.storage_name or field.name,
                index_type=INDEX_KIND_MAP[field.index_kind],
                metric_type=DISTANCE_FUNCTION_MAP[field.distance_function],
            )
        return schema, index_params

    @override
    async def ensure_collection_exists(self, **kwargs: Any) -> None:
        """Create the Milvus collection if it does not already exist.

        The schema is derived from the data model definition: the key field becomes the
        primary key, data fields become typed scalar fields and vector fields become
        ``FLOAT_VECTOR`` fields, each with an index. The dynamic field is enabled so that
        properties that are not part of the definition are preserved.
        """
        if await self.collection_exists():
            return
        schema, index_params = self._build_schema_and_index()
        await asyncio.to_thread(
            self.milvus_client.create_collection,
            collection_name=self.collection_name,
            schema=schema,
            index_params=index_params,
            **kwargs,
        )

    @override
    async def collection_exists(self, **kwargs: Any) -> bool:
        return await asyncio.to_thread(self.milvus_client.has_collection, self.collection_name, **kwargs)

    @override
    async def ensure_collection_deleted(self, **kwargs: Any) -> None:
        if await self.collection_exists():
            await asyncio.to_thread(self.milvus_client.drop_collection, self.collection_name, **kwargs)

    @override
    def _lambda_parser(self, node: ast.AST) -> str:
        # Milvus boolean expression language, see https://milvus.io/docs/boolean.md
        match node:
            case ast.Compare():
                if len(node.ops) > 1:
                    # Chain comparisons (e.g. 1 < x < 3) become an AND of each comparison.
                    values = []
                    for idx in range(len(node.ops)):
                        left = node.left if idx == 0 else node.comparators[idx - 1]
                        right = node.comparators[idx]
                        op = node.ops[idx]
                        values.append(self._lambda_parser(ast.Compare(left=left, ops=[op], comparators=[right])))
                    return f"({' and '.join(values)})"
                left_str = self._lambda_parser(node.left)
                right_str = self._lambda_parser(node.comparators[0])
                op = node.ops[0]
                match op:
                    case ast.Eq():
                        return f"({left_str} == {right_str})"
                    case ast.NotEq():
                        return f"({left_str} != {right_str})"
                    case ast.Gt():
                        return f"({left_str} > {right_str})"
                    case ast.GtE():
                        return f"({left_str} >= {right_str})"
                    case ast.Lt():
                        return f"({left_str} < {right_str})"
                    case ast.LtE():
                        return f"({left_str} <= {right_str})"
                    case ast.In():
                        return f"({left_str} in {right_str})"
                    case ast.NotIn():
                        return f"({left_str} not in {right_str})"
                raise NotImplementedError(f"Unsupported operator: {type(op)}")
            case ast.BoolOp():
                op_str = "and" if isinstance(node.op, ast.And) else "or"
                values = [self._lambda_parser(value) for value in node.values]
                return f"({f' {op_str} '.join(values)})"
            case ast.UnaryOp():
                match node.op:
                    case ast.Not():
                        operand = self._lambda_parser(node.operand)
                        return f"(not {operand})"
                    case ast.UAdd() | ast.USub() | ast.Invert():
                        raise NotImplementedError("Unary +, -, ~ are not supported in Milvus filters.")
            case ast.Attribute():
                if node.attr not in self.definition.storage_names:
                    raise VectorStoreOperationException(
                        f"Field '{node.attr}' not in data model (storage property names are used)."
                    )
                return node.attr
            case ast.Name():
                if node.id not in self.definition.storage_names:
                    raise VectorStoreOperationException(
                        f"Field '{node.id}' not in data model (storage property names are used)."
                    )
                return node.id
            case ast.Constant():
                return _format_constant(node.value)
            case ast.List():
                return "[" + ", ".join(self._lambda_parser(element) for element in node.elts) + "]"
        raise NotImplementedError(f"Unsupported AST node: {type(node)}")

    def _validate_data_model(self) -> None:
        super()._validate_data_model()
        if len(self.definition.vector_field_names) == 0:
            raise VectorStoreModelValidationError("Milvus requires at least one vector field.")

    @override
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        if self.managed_client:
            await asyncio.to_thread(self.milvus_client.close)


def _format_constant(value: Any) -> str:
    """Format a Python constant as a Milvus boolean expression literal."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return str(value)


@release_candidate
class MilvusStore(VectorStore):
    """A MilvusStore is a vector store that uses Milvus as the backend."""

    milvus_client: MilvusClient

    def __init__(
        self,
        uri: str | None = None,
        token: str | None = None,
        user: str | None = None,
        password: str | None = None,
        db_name: str | None = None,
        client: MilvusClient | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a new instance of the MilvusStore.

        Supply either a pre-built ``client`` or the connection parameters. When nothing is
        supplied the store connects to a local Milvus server at ``http://localhost:19530``.
        A local ``.db`` path can be passed as ``uri`` to use Milvus Lite.

        Args:
            uri: The URI of the Milvus server or a local Milvus Lite ``.db`` path.
            token: The token (or ``user:password``) used to authenticate.
            user: The username used to authenticate.
            password: The password used to authenticate.
            db_name: The Milvus database to use.
            client: A pre-built MilvusClient to use, if supplied the other connection
                parameters are ignored and the client is not closed by this store.
            embedding_generator: The embedding generator to use, optional.
            env_file_path: Use the environment settings file as a fallback to environment variables.
            env_file_encoding: The encoding of the environment settings file.
            **kwargs: Additional keyword arguments passed to the MilvusClient constructor.
        """
        if client:
            super().__init__(
                milvus_client=client, managed_client=False, embedding_generator=embedding_generator, **kwargs
            )
            return

        try:
            settings = MilvusSettings(
                uri=uri,
                token=token,
                user=user,
                password=password,
                db_name=db_name,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise VectorStoreInitializationException("Failed to create Milvus settings.", ex) from ex
        try:
            client = MilvusClient(**_build_client_kwargs(settings), **kwargs)
        except Exception as ex:
            raise VectorStoreInitializationException("Failed to create Milvus client.", ex) from ex
        super().__init__(milvus_client=client, embedding_generator=embedding_generator)

    @override
    def get_collection(
        self,
        record_type: type[TModel],
        *,
        definition: VectorStoreCollectionDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        **kwargs: Any,
    ) -> MilvusCollection:
        return MilvusCollection(
            record_type=record_type,
            definition=definition,
            collection_name=collection_name,
            client=self.milvus_client,
            embedding_generator=embedding_generator or self.embedding_generator,
            **kwargs,
        )

    @override
    async def list_collection_names(self, **kwargs: Any) -> Sequence[str]:
        return await asyncio.to_thread(self.milvus_client.list_collections, **kwargs)

    @override
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        if self.managed_client:
            await asyncio.to_thread(self.milvus_client.close)
