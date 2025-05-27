# Copyright (c) Microsoft. All rights reserved.

import ast
import logging
import sys
from collections.abc import Sequence
from inspect import isawaitable
from typing import Any, ClassVar, Final, Generic, TypeVar

from pinecone import IndexModel, Metric, PineconeAsyncio, ServerlessSpec, Vector
from pinecone.data.index_asyncio import _IndexAsyncio as IndexAsyncio
from pinecone.grpc import GRPCIndex, GRPCVector, PineconeGRPC
from pydantic import SecretStr, ValidationError

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.data.vector import (
    DistanceFunction,
    GetFilteredRecordOptions,
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
    _get_collection_name_from_model,
)
from semantic_kernel.exceptions.vector_store_exceptions import (
    VectorStoreInitializationException,
    VectorStoreModelException,
    VectorStoreOperationException,
)
from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.kernel_types import OneOrMany
from semantic_kernel.utils.feature_stage_decorator import release_candidate

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

logger = logging.getLogger(__name__)

TKey = TypeVar("TKey", bound=str)

DISTANCE_METRIC_MAP: Final[dict[DistanceFunction, Metric]] = {
    DistanceFunction.COSINE_SIMILARITY: Metric.COSINE,
    DistanceFunction.EUCLIDEAN_DISTANCE: Metric.EUCLIDEAN,
    DistanceFunction.DOT_PROD: Metric.DOTPRODUCT,
    DistanceFunction.DEFAULT: Metric.COSINE,
}


class PineconeSettings(KernelBaseSettings):
    """Pinecone model settings.

    Args:
    - api_key: SecretStr - Pinecone API key
        (Env var PINECONE_API_KEY)
    - namespace: str - Pinecone namespace (optional, default is "")
    - embed_model: str - Embedding model (optional, default is None)
        (Env var PINECONE_EMBED_MODEL)
    """

    env_prefix: ClassVar[str] = "PINECONE_"

    api_key: SecretStr
    namespace: str = ""
    embed_model: str | None = None


@release_candidate
class PineconeCollection(
    VectorStoreCollection[TKey, TModel],
    VectorSearch[TKey, TModel],
    Generic[TKey, TModel],
):
    """Interact with a Pinecone Index."""

    client: PineconeGRPC | PineconeAsyncio
    namespace: str = ""
    index: IndexModel | None = None
    index_client: IndexAsyncio | GRPCIndex | None = None
    supported_key_types: ClassVar[set[str] | None] = {"str"}
    supported_search_types: ClassVar[set[SearchType]] = {SearchType.VECTOR}
    embed_settings: dict[str, Any] | None = None

    def __init__(
        self,
        record_type: type[TModel],
        definition: VectorStoreCollectionDefinition | None = None,
        collection_name: str | None = None,
        client: PineconeGRPC | PineconeAsyncio | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        embed_model: str | None = None,
        embed_settings: dict[str, Any] | None = None,
        use_grpc: bool = False,
        api_key: str | None = None,
        namespace: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        **kwargs: str,
    ) -> None:
        """Initialize the Pinecone collection.

        Args:
            record_type: The type of the data model.
            definition: The definition of the data model.
            collection_name: The name of the Pinecone collection.
            client: The Pinecone client to use. If not provided, a new client will be created.
            use_grpc: Whether to use the GRPC client or not. Default is False.
            embedding_generator: The embedding generator to use. If not provided, it will be read from the environment.
            embed_model: The settings for the embedding model. If not provided, it will be read from the environment.
                This cannot be combined with a GRPC client.
            embed_settings: The settings for the embedding model. If not provided, the model can be read
            from the environment.
                The other settings are created based on the data model.
                See the pinecone documentation for more details.
                This cannot be combined with a GRPC client.
            api_key: The Pinecone API key. If not provided, it will be read from the environment.
            namespace: The namespace to use. Default is "".
            env_file_path: The path to the environment file. If not provided, it will be read from the default location.
            env_file_encoding: The encoding of the environment file.
            kwargs: Additional arguments to pass to the Pinecone client.
        """
        if not collection_name:
            collection_name = _get_collection_name_from_model(record_type, definition)
        managed_client = not client
        try:
            settings = PineconeSettings(
                api_key=api_key,
                embed_model=embed_model,
                namespace=namespace,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as exc:
            raise VectorStoreInitializationException(f"Failed to create Pinecone settings: {exc}") from exc

        if embed_settings:
            if "model" not in embed_settings:
                embed_settings["model"] = settings.embed_model
            if settings.embed_model and embed_settings["model"] != settings.embed_model:
                logger.warning(
                    "The model in the embed_settings is different from the one in "
                    "the settings. The one in the settings will be used."
                )
        elif settings.embed_model:
            embed_settings = {
                "model": settings.embed_model,
            }
        if not client:
            if use_grpc:
                client = PineconeGRPC(
                    api_key=settings.api_key.get_secret_value(),
                    **kwargs,
                )
            else:
                client = PineconeAsyncio(
                    api_key=settings.api_key.get_secret_value(),
                    **kwargs,
                )

        super().__init__(
            collection_name=collection_name,
            record_type=record_type,
            definition=definition,
            client=client,
            embed_settings=embed_settings,
            namespace=settings.namespace,
            managed_client=managed_client,
            embedding_generator=embedding_generator,
            **kwargs,
        )

    def _validate_data_model(self):
        """Check if there is exactly one vector."""
        super()._validate_data_model()
        if len(self.definition.vector_field_names) > 1:
            raise VectorStoreInitializationException(
                "Pinecone only supports one (or zero when using the integrated inference) vector field. "
                "Please use a different data model or "
                f"remove {len(self.definition.vector_field_names) - 1} vector fields."
            )

    @override
    async def create_collection(self, **kwargs: Any) -> None:
        """Create the Pinecone collection.

        Args:
            kwargs: Additional arguments to pass to the Pinecone collection creation.
                - embed: if you want to support vectorizable text search,
                    you need to set this to a dict with the parameters
                    see https://docs.pinecone.io/guides/inference/understanding-inference
                    for more details.
                    Optionally, the `metric` and `field_map` will be filled based on the data model.
                    This can not be used with the GRPC client.
                - cloud: The cloud provider to use. Default is "aws".
                - region: The region to use. Default is "us-east-1".
        """
        vector_field = self.definition.vector_fields[0] if self.definition.vector_fields else None
        await (
            self._create_index_with_integrated_embeddings(vector_field, **kwargs)
            if self.embed_settings is not None or "embed" in kwargs
            else self._create_regular_index(vector_field, **kwargs)
        )

    async def _create_index_with_integrated_embeddings(
        self, vector_field: VectorStoreField | None, **kwargs: Any
    ) -> None:
        """Create the Pinecone index with the embed parameter."""
        if isinstance(self.client, PineconeGRPC):
            raise VectorStoreOperationException(
                "Pinecone GRPC client does not support integrated embeddings. Please use the Pinecone Asyncio client."
            )
        if self.embed_settings:
            embed = self.embed_settings.copy()
            embed.update(kwargs.pop("embed", {}))
        else:
            embed = kwargs.pop("embed", {})
        cloud = kwargs.pop("cloud", "aws")
        region = kwargs.pop("region", "us-east-1")
        if "metric" not in embed and vector_field:
            if vector_field.distance_function not in DISTANCE_METRIC_MAP:
                raise VectorStoreOperationException(
                    f"Distance function {vector_field.distance_function} is not supported by Pinecone."
                )
            embed["metric"] = DISTANCE_METRIC_MAP[vector_field.distance_function]
        if "field_map" not in embed:
            for field in self.definition.vector_fields:
                if not field.embedding_generator and not self.embedding_generator:
                    embed["field_map"] = {"text": field.storage_name or field.name}
                    break
        index_creation_args = {
            "name": self.collection_name,
            "cloud": cloud,
            "region": region,
            "embed": embed,
        }
        index_creation_args.update(kwargs)
        self.index = await self.client.create_index_for_model(**index_creation_args)
        await self._load_index_client()

    async def _create_regular_index(self, vector_field: VectorStoreField | None, **kwargs: Any) -> None:
        """Create the Pinecone index with the embed parameter."""
        if not vector_field:
            raise VectorStoreOperationException(
                "Pinecone collection needs a vector field, when not using the integrated embeddings."
            )
        if vector_field.distance_function not in DISTANCE_METRIC_MAP:
            raise VectorStoreOperationException(
                f"Distance function {vector_field.distance_function} is not supported by Pinecone."
            )
        cloud = kwargs.pop("cloud", "aws")
        region = kwargs.pop("region", "us-east-1")
        spec = kwargs.pop("spec", ServerlessSpec(cloud=cloud, region=region))
        index_creation_args = {
            "name": self.collection_name,
            "spec": spec,
            "dimension": vector_field.dimensions,
            "metric": DISTANCE_METRIC_MAP[vector_field.distance_function],
            "vector_type": "dense",
        }
        index_creation_args.update(kwargs)
        index = self.client.create_index(**index_creation_args)
        if isawaitable(index):
            index = await index
        self.index = index
        await self._load_index_client()

    async def _load_index_client(self) -> None:
        if not self.index:
            index = self.client.describe_index(self.collection_name)
            if isawaitable(index):
                index = await index
            self.index = index
        if self.index.embed is not None:
            if isinstance(self.client, PineconeGRPC):
                raise VectorStoreOperationException(
                    "Pinecone GRPC client does not support integrated embeddings. "
                    "Please use the Pinecone Asyncio client."
                )
            self.embed_settings = self.index.embed
        if not self.index_client:
            self.index_client = (
                self.client.IndexAsyncio(host=self.index.host)
                if isinstance(self.client, PineconeAsyncio)
                else self.client.Index(host=self.index.host)
            )

    @override
    async def does_collection_exist(self, **kwargs) -> bool:
        """Check if the Pinecone collection exists."""
        exists = (
            await self.client.has_index(self.collection_name)
            if isinstance(self.client, PineconeAsyncio)
            else self.client.has_index(self.collection_name)
        )
        if exists:
            await self._load_index_client()
        return exists

    @override
    async def ensure_collection_deleted(self, **kwargs: Any) -> None:
        """Delete the Pinecone collection."""
        if not await self.does_collection_exist():
            if self.index or self.index_client:
                self.index = None
                self.index_client = None
            return
        await self.client.delete_index(self.collection_name) if isinstance(
            self.client, PineconeAsyncio
        ) else self.client.delete_index(self.collection_name)
        self.index = None
        if self.index_client:
            await self.index_client.close() if isinstance(
                self.index_client, IndexAsyncio
            ) else self.index_client.close()
            self.index_client = None

    def _record_to_pinecone_vector(self, record: dict[str, Any]) -> Vector | GRPCVector | dict[str, Any]:
        """Convert a record to a Pinecone vector."""
        metadata_fields = self.definition.get_storage_names(include_key_field=False, include_vector_fields=False)
        vector_field = self.definition.vector_fields[0]
        if isinstance(self.client, PineconeGRPC):
            return GRPCVector(
                id=record[self._key_field_storage_name],
                values=record.get(vector_field.storage_name or vector_field.name, None),
                metadata={key: value for key, value in record.items() if key in metadata_fields},
            )
        if self.embed_settings is not None:
            record.pop(vector_field.storage_name or vector_field.name, None)
            record["_id"] = record.pop(self._key_field_name)
            return record
        return Vector(
            id=record[self._key_field_storage_name],
            values=record.get(vector_field.storage_name or vector_field.name, None) or list(),
            metadata={key: value for key, value in record.items() if key in metadata_fields},
        )

    def _pinecone_vector_to_record(self, record: Vector | dict[str, Any]) -> dict[str, Any]:
        """Convert a Pinecone vector to a record."""
        if isinstance(record, dict):
            record[self._key_field_storage_name] = record.pop("_id")
            return record
        vector_field = self.definition.vector_fields[0]
        ret_record = {
            self._key_field_storage_name: record.id,
            vector_field.storage_name or vector_field.name: record.values,
        }
        ret_record.update(record.metadata)
        return ret_record

    @override
    def _serialize_dicts_to_store_models(
        self, records: Sequence[dict[str, Any]], **kwargs: Any
    ) -> Sequence[Vector | GRPCVector | dict[str, Any]]:
        return [self._record_to_pinecone_vector(record) for record in records]

    @override
    def _deserialize_store_models_to_dicts(self, records: Sequence[Vector], **kwargs: Any) -> Sequence[dict[str, Any]]:
        return [self._pinecone_vector_to_record(record) for record in records]

    @override
    async def _inner_upsert(
        self,
        records: Sequence[Any],
        **kwargs: Any,
    ) -> Sequence[TKey]:
        """Upsert the records to the Pinecone collection."""
        if not self.index_client:
            await self._load_index_client()
        if not self.index_client:
            raise VectorStoreOperationException("Pinecone collection is not initialized.")
        if "namespace" not in kwargs:
            kwargs["namespace"] = self.namespace
        if self.embed_settings is not None:
            if isinstance(self.index_client, GRPCIndex):
                raise VectorStoreOperationException(
                    "Pinecone GRPC client does not support integrated embeddings. "
                    "Please use the Pinecone Asyncio client."
                )
            await self.index_client.upsert_records(records=records, **kwargs)
            return [record["_id"] for record in records]
        if isinstance(self.index_client, GRPCIndex):
            self.index_client.upsert(records, **kwargs)
        else:
            await self.index_client.upsert(records, **kwargs)
        return [record.id for record in records]

    @override
    async def _inner_get(
        self, keys: Sequence[TKey] | None = None, options: GetFilteredRecordOptions | None = None, **kwargs: Any
    ) -> OneOrMany[Any] | None:
        """Get the records from the Pinecone collection."""
        if not keys:
            if options is not None:
                raise NotImplementedError("Get without keys is not yet implemented.")
            return None
        if not self.index_client:
            await self._load_index_client()
        if not self.index_client:
            raise VectorStoreOperationException("Pinecone collection is not initialized.")
        namespace = kwargs.get("namespace", self.namespace)
        if isinstance(self.index_client, GRPCIndex):
            response = self.index_client.fetch(ids=keys, namespace=namespace)
        else:
            response = await self.index_client.fetch(ids=keys, namespace=namespace)
        return list(response.vectors.values())

    @override
    async def _inner_delete(self, keys: Sequence[TKey], **kwargs: Any) -> None:
        """Delete the records from the Pinecone collection."""
        if not self.index_client:
            await self._load_index_client()
        if not self.index_client:
            raise VectorStoreOperationException("Pinecone collection is not initialized.")
        if "namespace" not in kwargs:
            kwargs["namespace"] = self.namespace
        if isinstance(self.index_client, GRPCIndex):
            self.index_client.delete(ids=keys, **kwargs)
        else:
            await self.index_client.delete(ids=keys, **kwargs)

    @override
    async def _inner_search(
        self,
        search_type: SearchType,
        options: VectorSearchOptions,
        values: Any | None = None,
        vector: Sequence[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        """Search the records in the Pinecone collection."""
        if not self.index_client:
            await self._load_index_client()
        if not self.index_client:
            raise VectorStoreOperationException("Pinecone collection is not initialized.")
        if search_type != SearchType.VECTOR:
            raise VectorStoreOperationException(f"Search type {search_type} is not supported by Pinecone.")
        if "namespace" not in kwargs:
            kwargs["namespace"] = self.namespace
        vector_field = self.definition.try_get_vector_field(options.vector_property_name)
        if not vector_field:
            raise VectorStoreModelException(
                f"Vector field '{options.vector_property_name}' not found in the data model definition."
            )
        filter = self._build_filter(options.filter)
        # is embedded mode
        if self.embed_settings is not None:
            if not self.index_client or isinstance(self.index_client, GRPCIndex):
                raise VectorStoreOperationException(
                    "Pinecone GRPC client does not support integrated embeddings. "
                    "Please use the Pinecone Asyncio client."
                )
            search_args = {
                "query": {
                    "inputs": {"text": values},
                    "top_k": options.top,
                },
                "namespace": kwargs.get("namespace", self.namespace),
            }
            if filter:
                search_args["query"]["filter"] = {"$and": filter} if isinstance(filter, list) else filter
            results = await self.index_client.search_records(**search_args)
            return KernelSearchResults(
                results=self._get_vector_search_results_from_results(results.result.hits, options),
                total_count=len(results.result.hits),
            )
        if not vector:
            vector = await self._generate_vector_from_values(values, options)
        if not vector:
            raise VectorStoreOperationException("No vector found for the given values.")
        search_args = {
            "vector": vector,
            "top_k": options.top,
            "include_metadata": True,
            "include_values": options.include_vectors,
            "namespace": kwargs.get("namespace", self.namespace),
        }
        if filter:
            search_args["filter"] = {"$and": filter} if isinstance(filter, list) else filter
        results = self.index_client.query(**search_args)
        if isawaitable(results):
            results = await results
        return KernelSearchResults(
            results=self._get_vector_search_results_from_results(results.matches, options),
            total_count=len(results.matches),
        )

    @override
    def _lambda_parser(self, node: ast.AST) -> Any:
        # Comparison operations
        match node:
            case ast.Compare():
                if len(node.ops) > 1:
                    # Chain comparisons (e.g., 1 < x < 3) become $and of each comparison
                    values = []
                    for idx in range(len(node.ops)):
                        left = node.left if idx == 0 else node.comparators[idx - 1]
                        right = node.comparators[idx]
                        op = node.ops[idx]
                        values.append(self._lambda_parser(ast.Compare(left=left, ops=[op], comparators=[right])))
                    return {"$and": values}
                left = self._lambda_parser(node.left)
                right = self._lambda_parser(node.comparators[0])
                op = node.ops[0]
                match op:
                    case ast.In():
                        return {left: {"$in": right}}
                    case ast.NotIn():
                        return {left: {"$nin": right}}
                    case ast.Eq():
                        # Pinecone allows short form: {field: value}
                        return {left: right}
                    case ast.NotEq():
                        return {left: {"$ne": right}}
                    case ast.Gt():
                        return {left: {"$gt": right}}
                    case ast.GtE():
                        return {left: {"$gte": right}}
                    case ast.Lt():
                        return {left: {"$lt": right}}
                    case ast.LtE():
                        return {left: {"$lte": right}}
                raise NotImplementedError(f"Unsupported operator: {type(op)}")
            case ast.BoolOp():
                op = node.op  # type: ignore
                values = [self._lambda_parser(v) for v in node.values]
                if isinstance(op, ast.And):
                    return {"$and": values}
                if isinstance(op, ast.Or):
                    return {"$or": values}
                raise NotImplementedError(f"Unsupported BoolOp: {type(op)}")
            case ast.UnaryOp():
                match node.op:
                    case ast.Not():
                        operand = self._lambda_parser(node.operand)
                        # Pinecone only supports $not over $in (becomes $nin)
                        if (
                            isinstance(operand, dict)
                            and len(operand) == 1
                            and isinstance(next(operand.values()), dict)  # type: ignore
                            and "$in" in next(operand.values())  # type: ignore
                        ):
                            field = next(operand.keys())  # type: ignore
                            values = next(operand.values())["$in"]  # type: ignore
                            return {field: {"$nin": values}}
                        raise NotImplementedError(
                            "$not is only supported over $in (i.e., for ![...].contains(field)). "
                            "Other NOT expressions are not supported by Pinecone."
                        )
                    case ast.UAdd() | ast.USub() | ast.Invert():
                        raise NotImplementedError("Unary +, -, ~ are not supported in Pinecone filters.")
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
                if node.value is None:
                    raise NotImplementedError("Pinecone does not support null checks in vector search pre-filters.")
                return node.value
        raise NotImplementedError(f"Unsupported AST node: {type(node)}")

    @override
    def _get_record_from_result(self, result: dict[str, Any]) -> dict[str, Any]:
        if self.embed_settings is not None:
            return {"_id": result["_id"], **result["fields"]}
        return result

    @override
    def _get_score_from_result(self, result: Any) -> float | None:
        if self.embed_settings is not None:
            return result._score
        return result.score

    @override
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager."""
        if self.index_client:
            if isinstance(self.index_client, GRPCIndex):
                self.index_client.close()
            else:
                await self.index_client.close()
            self.index_client = None
        if isinstance(self.client, PineconeAsyncio) and self.managed_client:
            await self.client.close()


@release_candidate
class PineconeStore(VectorStore):
    """Pinecone Vector Store, for interacting with Pinecone collections."""

    client: PineconeGRPC | PineconeAsyncio

    def __init__(
        self,
        client: PineconeGRPC | PineconeAsyncio | None = None,
        api_key: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        use_grpc: bool = False,
        **kwargs: str,
    ) -> None:
        """Initialize the Pinecone store.

        Args:
            client: The Pinecone client to use. If not provided, a new client will be created.
            api_key: The Pinecone API key. If not provided, it will be read from the environment.
            embedding_generator: The embedding generator to use. If not provided, it will be read from the environment.
            env_file_path: The path to the environment file. If not provided, it will be read from the default location.
            env_file_encoding: The encoding of the environment file.
            use_grpc: Whether to use the GRPC client or not. Default is False.
            kwargs: Additional arguments to pass to the Pinecone client.

        """
        managed_client = not client
        if not client:
            try:
                settings = PineconeSettings(
                    api_key=api_key,
                    env_file_path=env_file_path,
                    env_file_encoding=env_file_encoding,
                )
            except ValidationError as exc:
                raise VectorStoreInitializationException(f"Failed to create Pinecone settings: {exc}") from exc

        if not client:
            if use_grpc:
                client = PineconeGRPC(
                    api_key=settings.api_key.get_secret_value(),
                    **kwargs,
                )
            else:
                client = PineconeAsyncio(
                    api_key=settings.api_key.get_secret_value(),
                    **kwargs,
                )
        super().__init__(
            client=client,
            managed_client=managed_client,
            embedding_generator=embedding_generator,
            **kwargs,
        )

    @override
    async def list_collection_names(self, **kwargs) -> Sequence[str]:
        """List the Pinecone collection names."""
        if isinstance(self.client, PineconeGRPC):
            return [idx.name for idx in self.client.list_indexes()]
        return [idx.name for idx in await self.client.list_indexes()]

    @override
    def get_collection(
        self,
        record_type: type[TModel],
        *,
        definition: VectorStoreCollectionDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        **kwargs: Any,
    ) -> PineconeCollection:
        return PineconeCollection(
            collection_name=collection_name,
            record_type=record_type,
            definition=definition,
            client=self.client,
            embedding_generator=embedding_generator or self.embedding_generator,
            **kwargs,
        )

    @override
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager."""
        if isinstance(self.client, PineconeAsyncio) and self.managed_client:
            await self.client.close()
