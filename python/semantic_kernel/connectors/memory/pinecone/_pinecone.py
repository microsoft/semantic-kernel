# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import Sequence
from inspect import isawaitable
from typing import Any, ClassVar, Generic

from pinecone import IndexModel, Metric, PineconeAsyncio, ServerlessSpec, Vector
from pinecone.data.index_asyncio import _IndexAsyncio as IndexAsyncio
from pinecone.grpc import GRPCIndex, GRPCVector, PineconeGRPC
from pydantic import ValidationError

from semantic_kernel.connectors.memory.pinecone.pinecone_settings import PineconeSettings
from semantic_kernel.data.const import DistanceFunction
from semantic_kernel.data.record_definition import (
    VectorStoreRecordDataField,
    VectorStoreRecordDefinition,
    VectorStoreRecordVectorField,
)
from semantic_kernel.data.text_search import KernelSearchResults
from semantic_kernel.data.vector_search import (
    VectorizableTextSearchMixin,
    VectorizedSearchMixin,
    VectorSearchFilter,
    VectorSearchOptions,
    VectorSearchResult,
)
from semantic_kernel.data.vector_storage import TKey, TModel, VectorStore, VectorStoreRecordCollection
from semantic_kernel.exceptions.vector_store_exceptions import (
    VectorStoreInitializationException,
    VectorStoreOperationException,
)
from semantic_kernel.kernel_types import OneOrMany

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

logger = logging.getLogger(__name__)


DISTANCE_METRIC_MAP = {
    DistanceFunction.COSINE_SIMILARITY: Metric.COSINE,
    DistanceFunction.EUCLIDEAN_DISTANCE: Metric.EUCLIDEAN,
    DistanceFunction.DOT_PROD: Metric.DOTPRODUCT,
}


class PineconeCollection(
    VectorStoreRecordCollection[TKey, TModel],
    VectorizedSearchMixin[TKey, TModel],
    VectorizableTextSearchMixin[TKey, TModel],
    Generic[TKey, TModel],
):
    """Interact with a Pinecone Index."""

    client: PineconeGRPC | PineconeAsyncio
    namespace: str = ""
    index: IndexModel | None = None
    index_client: IndexAsyncio | GRPCIndex | None = None
    supported_key_types: ClassVar[list[str] | None] = ["str"]
    embed_settings: dict[str, Any] | None = None

    def __init__(
        self,
        collection_name: str,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        client: PineconeGRPC | PineconeAsyncio | None = None,
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
            collection_name: The name of the Pinecone collection.
            data_model_type: The type of the data model.
            data_model_definition: The definition of the data model.
            client: The Pinecone client to use. If not provided, a new client will be created.
            use_grpc: Whether to use the GRPC client or not. Default is False.
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
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            client=client,
            embed_settings=embed_settings,
            namespace=settings.namespace,
            managed_client=managed_client,
            **kwargs,
        )

    def _validate_data_model(self):
        """Check if there is exactly one vector."""
        super()._validate_data_model()
        if len(self.data_model_definition.vector_field_names) > 1:
            raise VectorStoreInitializationException(
                "Pinecone only supports one (or zero when using the integrated inference) vector field. "
                "Please use a different data model or "
                f"remove {len(self.data_model_definition.vector_field_names) - 1} vector fields."
            )
        if len(self.data_model_definition.vector_field_names) == 0 and not self.embed_settings:
            logger.warning(
                "Pinecone collection does not have a vector field. "
                "Please use the integrated inference to create the vector field. "
                "Pass in the `embed` parameter to the collection creation method. "
                "See https://docs.pinecone.io/guides/inference/understanding-inference for more details."
            )
        if self.embed_settings is not None and not self.data_model_definition.vector_fields[0].local_embedding:
            raise VectorStoreInitializationException(
                "Pinecone collection with integrated inference only supports a non-local embedding field."
                "Change the `local_embedding` property to False in the data model."
                f"Field name: {self.data_model_definition.vector_field_names[0]}"
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
        vector_field = self.data_model_definition.vector_fields[0] if self.data_model_definition.vector_fields else None
        await (
            self._create_index_with_integrated_embeddings(vector_field, **kwargs)
            if self.embed_settings is not None or "embed" in kwargs
            else self._create_regular_index(vector_field, **kwargs)
        )

    async def _create_index_with_integrated_embeddings(
        self, vector_field: VectorStoreRecordVectorField | None, **kwargs: Any
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
        if "metric" not in embed:
            if vector_field and vector_field.distance_function:
                if vector_field.distance_function not in DISTANCE_METRIC_MAP:
                    raise VectorStoreOperationException(
                        f"Distance function {vector_field.distance_function} is not supported by Pinecone."
                    )
                embed["metric"] = DISTANCE_METRIC_MAP[vector_field.distance_function]
            else:
                logger.info("Metric not set, defaulting to cosine.")
                embed["metric"] = Metric.COSINE
        if "field_map" not in embed:
            for field in self.data_model_definition.fields.values():
                if isinstance(field, VectorStoreRecordDataField) and field.has_embedding:
                    embed["field_map"] = {"text": field.name}
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

    async def _create_regular_index(self, vector_field: VectorStoreRecordVectorField | None, **kwargs: Any) -> None:
        """Create the Pinecone index with the embed parameter."""
        if not vector_field:
            raise VectorStoreOperationException(
                "Pinecone collection needs a vector field, when not using the integrated embeddings."
            )
        if vector_field.distance_function:
            metric = DISTANCE_METRIC_MAP.get(vector_field.distance_function, None)
            if not metric:
                raise VectorStoreOperationException(
                    f"Distance function {vector_field.distance_function} is not supported by Pinecone."
                )
        else:
            metric = Metric.COSINE
        cloud = kwargs.pop("cloud", "aws")
        region = kwargs.pop("region", "us-east-1")
        spec = kwargs.pop("spec", ServerlessSpec(cloud=cloud, region=region))
        index_creation_args = {
            "name": self.collection_name,
            "spec": spec,
            "dimension": vector_field.dimensions,
            "metric": metric,
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
    async def delete_collection(self, **kwargs: Any) -> None:
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
        metadata_fields = self.data_model_definition.get_field_names(
            include_key_field=False, include_vector_fields=False
        )
        if isinstance(self.client, PineconeGRPC):
            return GRPCVector(
                id=record[self._key_field_name],
                values=record.get(self.data_model_definition.vector_field_names[0], None),
                metadata={key: value for key, value in record.items() if key in metadata_fields},
            )
        if self.embed_settings is not None:
            record.pop(self.data_model_definition.vector_field_names[0], None)
            record["_id"] = record.pop(self._key_field_name)
            return record
        return Vector(
            id=record[self._key_field_name],
            values=record.get(self.data_model_definition.vector_field_names[0], None) or list(),
            metadata={key: value for key, value in record.items() if key in metadata_fields},
        )

    def _pinecone_vector_to_record(self, record: Vector | dict[str, Any]) -> dict[str, Any]:
        """Convert a Pinecone vector to a record."""
        if isinstance(record, dict):
            record[self._key_field_name] = record.pop("_id")
            return record
        ret_record = {self._key_field_name: record.id, self.data_model_definition.vector_field_names[0]: record.values}
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
    async def _inner_get(self, keys: Sequence[TKey], **kwargs: Any) -> OneOrMany[Any] | None:
        """Get the records from the Pinecone collection."""
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
        options: VectorSearchOptions,
        search_text: str | None = None,
        vectorizable_text: str | None = None,
        vector: list[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        """Search the records in the Pinecone collection."""
        if not self.index_client:
            await self._load_index_client()
        if not self.index_client:
            raise VectorStoreOperationException("Pinecone collection is not initialized.")
        if "namespace" not in kwargs:
            kwargs["namespace"] = self.namespace
        if vector is not None:
            if self.embed_settings is not None:
                raise VectorStoreOperationException(
                    "Pinecone collection only support vector search when integrated embeddings are used.",
                )
            return await self._inner_vectorized_search(vector, options, **kwargs)
        if vectorizable_text is not None:
            if self.embed_settings is None:
                raise VectorStoreOperationException(
                    "Pinecone collection only support vectorizable text search when integrated embeddings are used.",
                )
            return await self._inner_vectorizable_text_search(vectorizable_text, options, **kwargs)

        raise VectorStoreOperationException(
            "Pinecone collection does not support text search. Please provide a vector.",
        )

    async def _inner_vectorizable_text_search(
        self,
        vectorizable_text: str,
        options: VectorSearchOptions,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        if not self.index_client or isinstance(self.index_client, GRPCIndex):
            raise VectorStoreOperationException(
                "Pinecone GRPC client does not support integrated embeddings. Please use the Pinecone Asyncio client."
            )
        search_args = {
            "query": {"inputs": {"text": vectorizable_text}, "top_k": options.top},
            "namespace": kwargs.get("namespace", self.namespace),
        }
        if options.filter:
            search_args["query"]["filter"] = self._build_filter(options.filter)

        results = await self.index_client.search_records(**search_args)
        return KernelSearchResults(
            results=self._get_vector_search_results_from_results(results.result.hits, options),
            total_count=len(results.result.hits),
        )

    async def _inner_vectorized_search(
        self, vector: list[float | int], options: VectorSearchOptions, **kwargs: Any
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        """Search the records in the Pinecone collection."""
        assert self.index_client is not None  # nosec
        search_args = {
            "vector": vector,
            "top_k": options.top,
            "include_metadata": True,
            "include_values": options.include_vectors,
            "namespace": kwargs.get("namespace", self.namespace),
        }
        if options.filter:
            search_args["filter"] = self._build_filter(options.filter)
        results = self.index_client.query(**search_args)
        if isawaitable(results):
            results = await results
        return KernelSearchResults(
            results=self._get_vector_search_results_from_results(results.matches, options),
            total_count=len(results.matches),
        )

    def _build_filter(self, filters: VectorSearchFilter) -> dict[str, Any]:
        """Build the filter for the Pinecone collection."""
        ret_filter: dict[str, Any] = {}
        ret_filter = {"$and": []}
        for filter in filters.filters:
            ret_filter["$and"].append({filter.field_name: {"$eq": filter.value}})
        if len(ret_filter["$and"]) == 0:
            return {}
        if len(ret_filter["$and"]) == 1:
            return ret_filter["$and"][0]
        return ret_filter

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


class PineconeStore(VectorStore):
    """Pinecone Vector Store, for interacting with Pinecone collections."""

    client: PineconeGRPC | PineconeAsyncio

    def __init__(
        self,
        client: PineconeGRPC | PineconeAsyncio | None = None,
        api_key: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        use_grpc: bool = False,
        **kwargs: str,
    ) -> None:
        """Initialize the Pinecone store.

        Args:
            client: The Pinecone client to use. If not provided, a new client will be created.
            api_key: The Pinecone API key. If not provided, it will be read from the environment.
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
        collection_name: str,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        **kwargs: Any,
    ) -> "VectorStoreRecordCollection":
        """Create the Pinecone collection."""
        return PineconeCollection(
            collection_name=collection_name,
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            client=self.client,
            **kwargs,
        )

    @override
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager."""
        if isinstance(self.client, PineconeAsyncio) and self.managed_client:
            await self.client.close()
