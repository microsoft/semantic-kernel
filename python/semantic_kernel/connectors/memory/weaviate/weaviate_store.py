# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import Sequence
from typing import Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

import weaviate
from weaviate.classes.init import Auth
from weaviate.exceptions import WeaviateConnectionError

from semantic_kernel.connectors.memory.weaviate.weaviate_collection import WeaviateCollection
from semantic_kernel.connectors.memory.weaviate.weaviate_settings import WeaviateSettings
from semantic_kernel.data.record_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_storage import VectorStore, VectorStoreRecordCollection
from semantic_kernel.exceptions import (
    VectorStoreException,
    VectorStoreInitializationException,
    VectorStoreOperationException,
)
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class WeaviateStore(VectorStore):
    """A Weaviate store is a vector store that uses Weaviate as the backend."""

    async_client: weaviate.WeaviateAsyncClient

    def __init__(
        self,
        url: str | None = None,
        api_key: str | None = None,
        local_host: str | None = None,
        local_port: int | None = None,
        local_grpc_port: int | None = None,
        use_embed: bool = False,
        async_client: weaviate.WeaviateAsyncClient | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ):
        """Initialize a Weaviate collection.

        Args:
            url: The Weaviate URL
            api_key: The Weaviate API key.
            local_host: The local Weaviate host (i.e. Weaviate in a Docker container).
            local_port: The local Weaviate port.
            local_grpc_port: The local Weaviate gRPC port.
            use_embed: Whether to use the client embedding options.
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
                    async_client = weaviate.use_async_with_weaviate_cloud(
                        cluster_url=str(weaviate_settings.url),
                        auth_credentials=Auth.api_key(weaviate_settings.api_key.get_secret_value()),
                    )
                elif weaviate_settings.local_host:
                    kwargs = {
                        "port": weaviate_settings.local_port,
                        "grpc_port": weaviate_settings.local_grpc_port,
                    }
                    kwargs = {k: v for k, v in kwargs.items() if v is not None}
                    async_client = weaviate.use_async_with_local(
                        host=weaviate_settings.local_host,
                        **kwargs,
                    )
                elif weaviate_settings.use_embed:
                    async_client = weaviate.use_async_with_embedded()
                else:
                    raise NotImplementedError(
                        "Weaviate settings must specify either a custom client, a Weaviate Cloud instance,",
                        " a local Weaviate instance, or the client embedding options.",
                    )
            except Exception as e:
                raise VectorStoreInitializationException(f"Failed to initialize Weaviate client: {e}")

        super().__init__(async_client=async_client, managed_client=managed_client)

    @override
    def get_collection(
        self,
        collection_name: str,
        data_model_type: type[object],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        **kwargs: Any,
    ) -> VectorStoreRecordCollection:
        if collection_name not in self.vector_record_collections:
            self.vector_record_collections[collection_name] = WeaviateCollection(
                data_model_type=data_model_type,
                collection_name=collection_name,
                data_model_definition=data_model_definition,
                async_client=self.async_client,
                **kwargs,
            )
        return self.vector_record_collections[collection_name]

    @override
    async def list_collection_names(self, **kwargs) -> Sequence[str]:
        async with self.async_client:
            try:
                collections = await self.async_client.collections.list_all()
                return [collection.name for collection in collections]
            except Exception as e:
                raise VectorStoreOperationException(f"Failed to list Weaviate collections: {e}")

    @override
    async def __aenter__(self) -> "VectorStore":
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
