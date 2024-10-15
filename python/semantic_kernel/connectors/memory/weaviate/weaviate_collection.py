# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import Sequence
from typing import Any, TypeVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

import weaviate
from pydantic import field_validator
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter
from weaviate.collections.classes.data import DataObject
from weaviate.collections.collection import CollectionAsync

from semantic_kernel.connectors.memory.weaviate.utils import (
    data_model_definition_to_weaviate_named_vectors,
    data_model_definition_to_weaviate_properties,
    extract_key_from_dict_record_based_on_data_model_definition,
    extract_key_from_weaviate_object_based_on_data_model_definition,
    extract_properties_from_dict_record_based_on_data_model_definition,
    extract_properties_from_weaviate_object_based_on_data_model_definition,
    extract_vectors_from_dict_record_based_on_data_model_definition,
    extract_vectors_from_weaviate_object_based_on_data_model_definition,
)
from semantic_kernel.connectors.memory.weaviate.weaviate_settings import WeaviateSettings
from semantic_kernel.data.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_store_record_collection import VectorStoreRecordCollection
from semantic_kernel.data.vector_store_record_fields import VectorStoreRecordDataField
from semantic_kernel.exceptions.memory_connector_exceptions import (
    MemoryConnectorException,
    MemoryConnectorInitializationError,
)
from semantic_kernel.kernel_types import OneOrMany
from semantic_kernel.utils.experimental_decorator import experimental_class

TModel = TypeVar("TModel")
TKey = TypeVar("TKey", str, int)


@experimental_class
class WeaviateCollection(VectorStoreRecordCollection[TKey, TModel]):
    """A Weaviate collection is a collection of records that are stored in a Weaviate database."""

    async_client: weaviate.WeaviateAsyncClient

    def __init__(
        self,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition,
        collection_name: str,
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
            data_model_type: The type of the data model.
            data_model_definition: The definition of the data model.
            collection_name: The name of the collection.
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
        if not async_client:
            weaviate_settings = WeaviateSettings.create(
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
                raise MemoryConnectorInitializationError(f"Failed to initialize Weaviate client: {e}")

        super().__init__(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=collection_name,
            async_client=async_client,
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

        async with self.async_client:
            try:
                collection: CollectionAsync = self.async_client.collections.get(self.collection_name)
                response = await collection.data.insert_many(records)
            except Exception as ex:
                raise MemoryConnectorException(f"Failed to upsert records: {ex}")

        return [str(v) for _, v in response.uuids.items()]

    @override
    async def _inner_get(self, keys: Sequence[TKey], **kwargs: Any) -> OneOrMany[Any] | None:
        include_vectors: bool = kwargs.get("include_vectors", False)
        named_vectors: list[str] = []
        if include_vectors:
            named_vectors = [
                data_field.name
                for data_field in self.data_model_definition.fields.values()
                if isinstance(data_field, VectorStoreRecordDataField) and data_field.has_embedding
            ]

        async with self.async_client:
            try:
                collection: CollectionAsync = self.async_client.collections.get(self.collection_name)
                result = await collection.query.fetch_objects(
                    filters=Filter.any_of([Filter.by_id().equal(key) for key in keys]),
                    # Requires a list of named vectors if it is not empty. Otherwise, a boolean is sufficient.
                    include_vector=named_vectors or include_vectors,
                )

                return result.objects
            except Exception as ex:
                raise MemoryConnectorException(f"Failed to get records: {ex}")

    @override
    async def _inner_delete(self, keys: Sequence[TKey], **kwargs: Any) -> None:
        async with self.async_client:
            try:
                collection: CollectionAsync = self.async_client.collections.get(self.collection_name)
                await collection.data.delete_many(where=Filter.any_of([Filter.by_id().equal(key) for key in keys]))
            except Exception as ex:
                raise MemoryConnectorException(f"Failed to delete records: {ex}")

    @override
    def _serialize_dicts_to_store_models(self, records: Sequence[dict[str, Any]], **kwargs: Any) -> Sequence[Any]:
        """Create a data object from a record based on the data model definition."""
        records_in_store_model: list[DataObject] = []
        for record in records:
            properties = extract_properties_from_dict_record_based_on_data_model_definition(
                record, self.data_model_definition
            )
            # If key is None, Weaviate will generate a UUID
            key = extract_key_from_dict_record_based_on_data_model_definition(record, self.data_model_definition)
            vectors = extract_vectors_from_dict_record_based_on_data_model_definition(
                record, self.data_model_definition
            )
            records_in_store_model.append(DataObject(properties=properties, uuid=key, vector=vectors))
        return records_in_store_model

    @override
    def _deserialize_store_models_to_dicts(self, records: Sequence[Any], **kwargs: Any) -> Sequence[dict[str, Any]]:
        records_in_dict: list[dict[str, Any]] = []
        for record in records:
            properties = extract_properties_from_weaviate_object_based_on_data_model_definition(
                record, self.data_model_definition
            )
            key = extract_key_from_weaviate_object_based_on_data_model_definition(record, self.data_model_definition)
            vectors = extract_vectors_from_weaviate_object_based_on_data_model_definition(
                record, self.data_model_definition
            )

            records_in_dict.append(properties | key | vectors)

        return records_in_dict

    @override
    async def create_collection(self, **kwargs) -> None:
        """Create the collection in Weaviate.

        Args:
            **kwargs: Additional keyword arguments.
        """
        async with self.async_client:
            try:
                await self.async_client.collections.create(
                    self.collection_name,
                    properties=data_model_definition_to_weaviate_properties(self.data_model_definition),
                    vectorizer_config=data_model_definition_to_weaviate_named_vectors(self.data_model_definition),
                )
            except Exception as ex:
                raise MemoryConnectorException(f"Failed to create collection: {ex}")

    @override
    async def does_collection_exist(self, **kwargs) -> bool:
        """Check if the collection exists in Weaviate.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            bool: Whether the collection exists.
        """
        async with self.async_client:
            try:
                await self.async_client.collections.exists(self.collection_name)
                return True
            except Exception as ex:
                raise MemoryConnectorException(f"Failed to check if collection exists: {ex}")

    @override
    async def delete_collection(self, **kwargs) -> None:
        """Delete the collection in Weaviate.

        Args:
            **kwargs: Additional keyword arguments.
        """
        async with self.async_client:
            try:
                await self.async_client.collections.delete(self.collection_name)
            except Exception as ex:
                raise MemoryConnectorException(f"Failed to delete collection: {ex}")
