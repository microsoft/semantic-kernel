# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import Mapping, Sequence
from typing import Any, ClassVar, Generic

from pydantic import ValidationError
from qdrant_client.async_qdrant_client import AsyncQdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchAny, PointStruct, QueryResponse, ScoredPoint, VectorParams

from semantic_kernel.connectors.memory.qdrant.const import DISTANCE_FUNCTION_MAP, TYPE_MAPPER_VECTOR
from semantic_kernel.connectors.memory.qdrant.utils import AsyncQdrantClientWrapper
from semantic_kernel.data.record_definition import VectorStoreRecordDefinition, VectorStoreRecordVectorField
from semantic_kernel.data.text_search import KernelSearchResults
from semantic_kernel.data.vector_search import (
    VectorizedSearchMixin,
    VectorSearchOptions,
    VectorSearchResult,
)
from semantic_kernel.data.vector_storage import TKey, TModel, VectorStoreRecordCollection
from semantic_kernel.exceptions import (
    VectorSearchExecutionException,
    VectorStoreInitializationException,
    VectorStoreModelValidationError,
    VectorStoreOperationException,
)
from semantic_kernel.kernel_types import OneOrMany
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.telemetry.user_agent import APP_INFO, prepend_semantic_kernel_to_user_agent

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class QdrantCollection(
    VectorStoreRecordCollection[TKey, TModel],
    VectorizedSearchMixin[TKey, TModel],
    Generic[TKey, TModel],
):
    """A QdrantCollection is a memory collection that uses Qdrant as the backend."""

    qdrant_client: AsyncQdrantClient
    named_vectors: bool
    supported_key_types: ClassVar[list[str] | None] = ["str", "int"]
    supported_vector_types: ClassVar[list[str] | None] = ["float", "int"]

    def __init__(
        self,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        collection_name: str | None = None,
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
            data_model_type (type[TModel]): The type of the data model.
            data_model_definition (VectorStoreRecordDefinition): The model fields, optional.
            collection_name (str): The name of the collection, optional.
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
                data_model_type=data_model_type,
                data_model_definition=data_model_definition,
                collection_name=collection_name,
                qdrant_client=client,  # type: ignore
                named_vectors=named_vectors,  # type: ignore
                managed_client=False,
            )
            return

        from semantic_kernel.connectors.memory.qdrant.qdrant_settings import QdrantSettings

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
            client = AsyncQdrantClientWrapper(**settings.model_dump(exclude_none=True), **kwargs)
        except ValueError as ex:
            raise VectorStoreInitializationException("Failed to create Qdrant client.", ex) from ex
        super().__init__(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=collection_name,
            qdrant_client=client,
            named_vectors=named_vectors,
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
        return [record.id for record in records]

    @override
    async def _inner_get(self, keys: Sequence[TKey], **kwargs: Any) -> OneOrMany[Any] | None:
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
        options: VectorSearchOptions,
        search_text: str | None = None,
        vectorizable_text: str | None = None,
        vector: list[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        query_vector: tuple[str, list[float | int]] | list[float | int] | None = None
        if vector is not None:
            if self.named_vectors and options.vector_field_name:
                query_vector = (options.vector_field_name, vector)
            else:
                query_vector = vector
        if query_vector is None:
            raise VectorSearchExecutionException("Search requires a vector.")
        results = await self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=self._create_filter(options),
            with_vectors=options.include_vectors,
            limit=options.top,
            offset=options.skip,
            **kwargs,
        )
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

    def _create_filter(self, options: VectorSearchOptions) -> Filter:
        return Filter(
            must=[
                FieldCondition(key=filter.field_name, match=MatchAny(any=[filter.value]))
                for filter in options.filter.filters
            ]
        )

    @override
    def _serialize_dicts_to_store_models(
        self,
        records: Sequence[dict[str, Any]],
        **kwargs: Any,
    ) -> Sequence[PointStruct]:
        return [
            PointStruct(
                id=record.pop(self._key_field_name),
                vector=record.pop(self.data_model_definition.vector_field_names[0])
                if not self.named_vectors
                else {field: record.pop(field) for field in self.data_model_definition.vector_field_names},
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
                    else {self.data_model_definition.vector_field_names[0]: record.vector}
                ),
            }
            for record in records
        ]

    @override
    async def create_collection(self, **kwargs) -> None:
        """Create a new collection in Azure AI Search.

        Args:
            **kwargs: Additional keyword arguments.
                You can supply all keyword arguments supported by the QdrantClient.create_collection method.
                This method creates the vectors_config automatically when not supplied, other params are not set.
                Collection name will be set to the collection_name property, cannot be overridden.
        """
        if "vectors_config" not in kwargs:
            vectors_config: VectorParams | Mapping[str, VectorParams] = {}
            if self.named_vectors:
                for field in self.data_model_definition.vector_field_names:
                    vector = self.data_model_definition.fields[field]
                    assert isinstance(vector, VectorStoreRecordVectorField)  # nosec
                    if not vector.dimensions:
                        raise VectorStoreOperationException("Vector field must have dimensions.")
                    vectors_config[field] = VectorParams(
                        size=vector.dimensions,
                        distance=DISTANCE_FUNCTION_MAP[vector.distance_function or "default"],
                        datatype=TYPE_MAPPER_VECTOR[vector.property_type or "default"],
                    )
            else:
                vector = self.data_model_definition.fields[self.data_model_definition.vector_field_names[0]]
                assert isinstance(vector, VectorStoreRecordVectorField)  # nosec
                if not vector.dimensions:
                    raise VectorStoreOperationException("Vector field must have dimensions.")
                vectors_config = VectorParams(
                    size=vector.dimensions,
                    distance=DISTANCE_FUNCTION_MAP[vector.distance_function or "default"],
                    datatype=TYPE_MAPPER_VECTOR[vector.property_type or "default"],
                )
            kwargs["vectors_config"] = vectors_config
        if "collection_name" not in kwargs:
            kwargs["collection_name"] = self.collection_name
        await self.qdrant_client.create_collection(**kwargs)

    @override
    async def does_collection_exist(self, **kwargs) -> bool:
        return await self.qdrant_client.collection_exists(self.collection_name, **kwargs)

    @override
    async def delete_collection(self, **kwargs) -> None:
        await self.qdrant_client.delete_collection(self.collection_name, **kwargs)

    def _validate_data_model(self):
        """Internal function that should be overloaded by child classes to validate datatypes, etc.

        This should take the VectorStoreRecordDefinition from the item_type and validate it against the store.

        Checks should include, allowed naming of parameters, allowed data types, allowed vector dimensions.
        """
        super()._validate_data_model()
        if len(self.data_model_definition.vector_field_names) > 1 and not self.named_vectors:
            raise VectorStoreModelValidationError("Only one vector field is allowed when not using named vectors.")

    @override
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager."""
        if self.managed_client:
            await self.qdrant_client.close()
