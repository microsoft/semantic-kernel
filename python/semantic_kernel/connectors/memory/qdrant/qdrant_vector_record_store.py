# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from typing import Any, TypeVar

from qdrant_client.async_qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct, UpdateStatus

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

from semantic_kernel.connectors.memory.qdrant.qdrant_settings import QdrantSettings
from semantic_kernel.connectors.telemetry import APP_INFO, prepend_semantic_kernel_to_user_agent
from semantic_kernel.data.models.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_store_record_collection import VectorStoreRecordCollection
from semantic_kernel.exceptions import ServiceResponseException
from semantic_kernel.exceptions.memory_connector_exceptions import MemoryConnectorInitializationError
from semantic_kernel.kernel import Kernel
from semantic_kernel.kernel_types import OneOrMany
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)

TModel = TypeVar("TModel")
TKey = TypeVar("TKey", str, int)


@experimental_class
class QdrantVectorRecordStore(VectorStoreRecordCollection[str | int, TModel]):
    def __init__(
        self,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        collection_name: str | None = None,
        kernel: Kernel | None = None,
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
            kernel: Kernel to use for embedding generation.
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
        super().__init__(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=collection_name,
            kernel=kernel,
        )
        if client:
            self._qdrant_client = client
            return
        settings = QdrantSettings.create(
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
        try:
            if APP_INFO:
                kwargs.setdefault("metadata", {})
                kwargs["metadata"] = prepend_semantic_kernel_to_user_agent(kwargs["metadata"])
            self._qdrant_client = AsyncQdrantClient(**settings.model_dump(exclude_none=True), **kwargs)
        except ValueError as ex:
            raise MemoryConnectorInitializationError("Failed to create Qdrant client.", ex) from ex

    async def close(self) -> None:
        """Closes the Qdrant client."""
        await self._qdrant_client.close()

    @override
    async def _inner_upsert(
        self,
        records: list[PointStruct],
        collection_name: str | None = None,
        **kwargs: Any,
    ) -> list[TKey]:
        result = await self._qdrant_client.upsert(
            collection_name=self.collection_name,
            points=records,
            **kwargs,
        )
        if result.status == UpdateStatus.COMPLETED:
            return [record.id for record in records]
        raise ServiceResponseException("Upsert failed")

    @override
    async def _inner_get(self, keys: list[TKey], **kwargs: Any) -> OneOrMany[Any] | None:
        if "with_vectors" not in kwargs:
            kwargs["with_vectors"] = True
        return await self._qdrant_client.retrieve(
            collection_name=self.collection_name,
            ids=keys,
            **kwargs,
        )

    @override
    async def _inner_delete(self, keys: list[TKey], **kwargs: Any) -> None:
        result = await self._qdrant_client.delete(
            collection_name=self.collection_name,
            points_selector=keys,
            **kwargs,
        )
        if result.status != UpdateStatus.COMPLETED:
            raise ServiceResponseException("Delete failed")

    @override
    def _serialize_dicts_to_store_models(
        self,
        records: list[dict[str, Any]],
        **kwargs: Any,
    ) -> list[PointStruct]:
        return [
            PointStruct(
                id=record.pop(self._key_field),
                # TODO (eavanvalkenburg): deal with non-named vectors
                vector={field: record.pop(field) for field in self._data_model_definition.vector_fields},
                payload=record,
            )
            for record in records
        ]

    @override
    def _deserialize_store_models_to_dicts(
        self,
        records: list[PointStruct],
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        return [
            {
                self._key_field: record.id,
                **record.payload,
                **record.vector,
            }
            for record in records
        ]  # type: ignore

    @override
    @property
    def supported_key_types(self) -> list[type] | None:
        return [str, int]

    @override
    @property
    def supported_vector_types(self) -> list[type] | None:
        return [list[float]]
