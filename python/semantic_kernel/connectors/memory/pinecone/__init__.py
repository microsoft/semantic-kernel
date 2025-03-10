# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import Sequence
from typing import Any, ClassVar, Generic, TypeVar

from semantic_kernel.data.const import DistanceFunction

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from pinecone import AzureRegion, CloudProvider, IndexModel, Metric, Pinecone, PineconeAsyncio, ServerlessSpec, Vector
from pinecone.data.index_asyncio import _IndexAsyncio as IndexAsyncio
from pinecone.grpc import GRPCIndex, PineconeGRPC

from semantic_kernel.connectors.memory.pinecone.pinecone_memory_store import (
    PineconeMemoryStore,
)
from semantic_kernel.connectors.memory.pinecone.pinecone_settings import PineconeSettings
from semantic_kernel.data.kernel_search_results import KernelSearchResults
from semantic_kernel.data.record_definition.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_search.vector_search import VectorSearchBase
from semantic_kernel.data.vector_search.vector_search_options import VectorSearchOptions
from semantic_kernel.data.vector_search.vector_search_result import VectorSearchResult
from semantic_kernel.data.vector_search.vectorized_search import VectorizedSearchMixin
from semantic_kernel.data.vector_storage.vector_store import VectorStore
from semantic_kernel.data.vector_storage.vector_store_record_collection import VectorStoreRecordCollection
from semantic_kernel.exceptions.vector_store_exceptions import (
    VectorStoreInitializationException,
    VectorStoreOperationException,
)

__all__ = ["PineconeMemoryStore", "PineconeSettings"]

TKey = TypeVar("TKey", bound="str")
TModel = TypeVar("TModel")


DISTANCE_METRIC_MAP = {
    DistanceFunction.COSINE_SIMILARITY: Metric.COSINE,
    DistanceFunction.EUCLIDEAN_DISTANCE: Metric.EUCLIDEAN,
    DistanceFunction.DOT_PROD: Metric.DOTPRODUCT,
}


class PineconeCollection(VectorSearchBase[TKey, TModel], VectorizedSearchMixin[TModel], Generic[TKey, TModel]):
    """Pinecone collection class.

    This class is used to create a Pinecone collection.
    """

    client: PineconeGRPC | PineconeAsyncio
    namespace: str = ""
    index: IndexModel | None = None
    index_client: IndexAsyncio | GRPCIndex | None = None
    supported_key_types: ClassVar[list[str] | None] = ["str"]

    def __init__(
        self,
        collection_name: str,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        client: PineconeGRPC | PineconeAsyncio | None = None,
        use_grpc: bool = False,
        api_key: str | None = None,
        namespace: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        **kwargs: str,
    ) -> None:
        """Initialize the Pinecone collection."""
        managed_client = not client

        settings = PineconeSettings(
            api_key=api_key,
            namespace=namespace,
            env_file_path=env_file_path,
            env_file_encoding=env_file_encoding,
        )

        if not settings.api_key:
            raise VectorStoreInitializationException("Pinecone API key is required.")

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
            namespace=settings.namespace,
            managed_client=managed_client,
            **kwargs,
        )

    @override
    async def create_collection(self, **kwargs: Any) -> None:
        """Create the Pinecone collection.

        Args:
            kwargs: Additional arguments to pass to the Pinecone collection creation."
        """
        cloud = kwargs.get("cloud", CloudProvider.AZURE)
        region = kwargs.get("region", AzureRegion.EASTUS2)

        vector = self.data_model_definition.vector_fields[0]
        if vector.distance_function:
            metric = DISTANCE_METRIC_MAP.get(vector.distance_function, None)
            if not metric:
                raise VectorStoreOperationException(
                    f"Distance function {vector.distance_function} is not supported by Pinecone."
                )
        else:
            metric = Metric.COSINE
        spec = kwargs.pop("spec", ServerlessSpec(cloud=cloud, region=region))
        index_creation_args = {
            "name": self.collection_name,
            "spec": spec,
            "dimensions": vector.dimensions,
            "metric": metric,
            "vector_type": "dense",
        }

        if isinstance(self.client, PineconeGRPC):
            self.index = self.client.create_index(**index_creation_args, **kwargs)
            self.index_client = self.client.Index(
                host=self.index.host,
                **kwargs,
            )
        else:
            self.index = await self.client.create_index(**index_creation_args, **kwargs)
            self.index_client = self.client.IndexAsyncio(
                host=self.index.host,
                **kwargs,
            )

    @override
    async def does_collection_exist(self, **kwargs) -> bool:
        """Check if the Pinecone collection exists."""
        if isinstance(self.client, PineconeGRPC):
            return self.client.has_index(self.collection_name)
        return await self.client.has_index(self.collection_name)

    @override
    async def delete_collection(self) -> None:
        """Delete the Pinecone collection."""
        if self.index:
            if isinstance(self.client, PineconeGRPC):
                self.client.delete_index(self.index.name)
            else:
                await self.client.delete_index(self.index.name)
            if isinstance(self.index_client, GRPCIndex):
                self.index_client.close()
            elif self.index_client is not None:
                await self.index_client.close()
            self.index = None
            self.index_client = None
        else:
            raise VectorStoreInitializationException("Pinecone collection not found.")

    def _record_to_pinecone_vector(self, record: dict[str, Any]) -> Vector:
        """Convert a record to a Pinecone vector."""
        metadata_fields = self.data_model_definition.get_field_names(
            include_key_field=False, include_vector_fields=False
        )
        return Vector(
            id=record[self._key_field_name],
            values=record[self.data_model_definition.vector_field_names[0]],
            metadata={key: value for key, value in record.items() if key not in metadata_fields},
        )

    def _pinecone_vector_to_record(self, vector: Vector) -> dict[str, Any]:
        """Convert a Pinecone vector to a record."""
        record = {self._key_field_name: vector.id, self.data_model_definition.vector_field_names[0]: vector.values}
        record.update(vector.metadata)
        return record

    @override
    def _serialize_dicts_to_store_models(self, records: Sequence[dict[str, Any]], **kwargs: Any) -> Sequence[Vector]:
        return [self._record_to_pinecone_vector(record) for record in records]

    @override
    def _deserialize_store_models_to_dicts(self, records: Sequence[Vector], **kwargs: Any) -> Sequence[dict[str, Any]]:
        return [self._pinecone_vector_to_record(record) for record in records]

    @override
    async def _inner_upsert(
        self,
        records: list[Vector],
        **kwargs: Any,
    ) -> None:
        """Upsert the records to the Pinecone collection."""
        if not self.index_client:
            raise VectorStoreInitializationException("Pinecone collection not found.")
        if "namespace" not in kwargs and self.namespace:
            kwargs["namespace"] = self.namespace
        if isinstance(self.index_client, GRPCIndex):
            self.index_client.upsert(records, **kwargs)
        else:
            await self.index_client.upsert(records, **kwargs)

    @override
    async def _inner_get(self, keys: Sequence[str], **kwargs: Any) -> Sequence[Vector]:
        """Get the records from the Pinecone collection."""
        if not self.index_client:
            raise VectorStoreInitializationException("Pinecone collection not found.")
        if "namespace" not in kwargs and self.namespace:
            kwargs["namespace"] = self.namespace
        if isinstance(self.index_client, GRPCIndex):
            response = self.index_client.fetch(ids=keys, **kwargs)
        else:
            response = await self.index_client.fetch(ids=keys, **kwargs)
        return response.vectors.values()

    @override
    async def _inner_delete(self, keys: Sequence[str], **kwargs: Any) -> None:
        """Delete the records from the Pinecone collection."""
        if not self.index_client:
            raise VectorStoreInitializationException("Pinecone collection not found.")
        if "namespace" not in kwargs and self.namespace:
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
            raise VectorStoreInitializationException("Pinecone collection not found.")
        if "namespace" not in kwargs and self.namespace:
            kwargs["namespace"] = self.namespace
        if vector is not None:
            if isinstance(self.index_client, GRPCIndex):
                results = self.index_client.query(
                    vector=vector,
                    top_k=options.top,
                    include_metadata=True,
                    include_values=options.include_vectors,
                    **kwargs,
                )
                return KernelSearchResults(
                    results=self._get_vector_search_results_from_results(results.matches, options),
                    total_count=len(results.matches),
                )
            results = await self.index_client.query(
                vector=vector,
                top_k=options.top,
                include_metadata=True,
                include_values=options.include_vectors,
                **kwargs,
            )
            return KernelSearchResults(
                results=self._get_vector_search_results_from_results(results.matches, options),
                total_count=len(results.matches),
            )
        raise VectorStoreOperationException(
            "Pinecone collection does not support text search. Please provide a vector.",
        )

    @override
    def _get_record_from_result(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    @override
    def _get_score_from_result(self, result: Any) -> float | None:
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


class PineconeStore(VectorStore):
    """Pinecone store class.

    This class is used to create a Pinecone store.
    """

    client: Pinecone

    def __init__(
        self,
        client: Pinecone | None = None,
        api_key: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        **kwargs: str,
    ) -> None:
        """Initialize the Pinecone store."""
        managed_client = not client
        if not client:
            from semantic_kernel.connectors.memory.pinecone.pinecone_settings import PineconeSettings

            settings = PineconeSettings(
                api_key=api_key,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )

        if not settings.api_key:
            raise VectorStoreInitializationException("Pinecone API key is required.")

        if not client:
            client = Pinecone(
                api_key=settings.api_key.get_secret_value(),
                **kwargs,
            )
        super().__init__(
            client=client,
            managed_client=managed_client,
            **kwargs,
        )

    @override
    def list_collection_names(self) -> list[str]:
        """List the Pinecone collection names."""
        return [idx.name for idx in self.client.list_indexes()]

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
