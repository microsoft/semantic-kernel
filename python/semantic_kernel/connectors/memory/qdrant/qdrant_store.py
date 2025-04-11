# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import ValidationError
from qdrant_client.async_qdrant_client import AsyncQdrantClient

from semantic_kernel.connectors.memory.qdrant.qdrant_collection import QdrantCollection
from semantic_kernel.data.record_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_storage import VectorStore
from semantic_kernel.exceptions import VectorStoreInitializationException
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.telemetry.user_agent import APP_INFO, prepend_semantic_kernel_to_user_agent

if TYPE_CHECKING:
    from semantic_kernel.data.vector_storage import VectorStoreRecordCollection

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

logger: logging.Logger = logging.getLogger(__name__)

TModel = TypeVar("TModel")
TKey = TypeVar("TKey", str, int)


@experimental
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
            super().__init__(qdrant_client=client, managed_client=False, **kwargs)
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
            client = AsyncQdrantClient(**settings.model_dump(exclude_none=True), **kwargs)
        except ValueError as ex:
            raise VectorStoreInitializationException("Failed to create Qdrant client.", ex) from ex
        super().__init__(qdrant_client=client)

    def get_collection(
        self,
        collection_name: str,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        **kwargs: Any,
    ) -> "VectorStoreRecordCollection":
        """Get a QdrantCollection tied to a collection.

        Args:
            collection_name (str): The name of the collection.
            data_model_type (type[TModel]): The type of the data model.
            data_model_definition (VectorStoreRecordDefinition | None): The model fields, optional.
            **kwargs: Additional keyword arguments, passed to the collection constructor.
        """
        if collection_name not in self.vector_record_collections:
            self.vector_record_collections[collection_name] = QdrantCollection(
                data_model_type=data_model_type,
                data_model_definition=data_model_definition,
                collection_name=collection_name,
                client=self.qdrant_client,
                **kwargs,
            )
        return self.vector_record_collections[collection_name]

    @override
    async def list_collection_names(self, **kwargs: Any) -> Sequence[str]:
        collections = await self.qdrant_client.get_collections()
        return [collection.name for collection in collections.collections]

    @override
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        if self.managed_client:
            await self.qdrant_client.close()
