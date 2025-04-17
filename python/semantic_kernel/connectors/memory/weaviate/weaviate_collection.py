# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import Sequence
from typing import Any, Generic

from pydantic import field_validator
from weaviate import WeaviateAsyncClient, use_async_with_embedded, use_async_with_local, use_async_with_weaviate_cloud
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter, MetadataQuery
from weaviate.collections.classes.data import DataObject
from weaviate.collections.collection import CollectionAsync
from weaviate.exceptions import WeaviateClosedClientError

from semantic_kernel.connectors.memory.weaviate.utils import (
    create_filter_from_vector_search_filters,
    data_model_definition_to_weaviate_named_vectors,
    data_model_definition_to_weaviate_properties,
    extract_key_from_dict_record_based_on_data_model_definition,
    extract_key_from_weaviate_object_based_on_data_model_definition,
    extract_properties_from_dict_record_based_on_data_model_definition,
    extract_properties_from_weaviate_object_based_on_data_model_definition,
    extract_vectors_from_dict_record_based_on_data_model_definition,
    extract_vectors_from_weaviate_object_based_on_data_model_definition,
    to_weaviate_vector_index_config,
)
from semantic_kernel.connectors.memory.weaviate.weaviate_settings import WeaviateSettings
from semantic_kernel.data.record_definition import VectorStoreRecordDefinition, VectorStoreRecordVectorField
from semantic_kernel.data.text_search import KernelSearchResults
from semantic_kernel.data.vector_search import (
    VectorizableTextSearchMixin,
    VectorizedSearchMixin,
    VectorSearchOptions,
    VectorSearchResult,
    VectorTextSearchMixin,
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

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

logger = logging.getLogger(__name__)


@experimental
class WeaviateCollection(
    VectorStoreRecordCollection[TKey, TModel],
    VectorizedSearchMixin[TKey, TModel],
    VectorTextSearchMixin[TKey, TModel],
    VectorizableTextSearchMixin[TKey, TModel],
    Generic[TKey, TModel],
):
    """A Weaviate collection is a collection of records that are stored in a Weaviate database."""

    async_client: WeaviateAsyncClient
    named_vectors: bool = True

    def __init__(
        self,
        data_model_type: type[TModel],
        collection_name: str,
        data_model_definition: VectorStoreRecordDefinition | None = None,
        url: str | None = None,
        api_key: str | None = None,
        local_host: str | None = None,
        local_port: int | None = None,
        local_grpc_port: int | None = None,
        use_embed: bool = False,
        named_vectors: bool = True,
        async_client: WeaviateAsyncClient | None = None,
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
            named_vectors: Whether to use named vectors, or a single unnamed vector.
                In both cases the data model can be the same, but it has to have 1 vector
                field if named_vectors is False.
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
                    async_client = use_async_with_weaviate_cloud(
                        cluster_url=str(weaviate_settings.url),
                        auth_credentials=Auth.api_key(weaviate_settings.api_key.get_secret_value()),
                    )
                elif weaviate_settings.local_host:
                    kwargs = {
                        "port": weaviate_settings.local_port,
                        "grpc_port": weaviate_settings.local_grpc_port,
                    }
                    kwargs = {k: v for k, v in kwargs.items() if v is not None}
                    async_client = use_async_with_local(
                        host=weaviate_settings.local_host,
                        **kwargs,
                    )
                elif weaviate_settings.use_embed:
                    async_client = use_async_with_embedded()
                else:
                    raise NotImplementedError(
                        "Weaviate settings must specify either a custom client, a Weaviate Cloud instance,",
                        " a local Weaviate instance, or the client embedding options.",
                    )
            except Exception as e:
                raise VectorStoreInitializationException(f"Failed to initialize Weaviate client: {e}")

        super().__init__(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=collection_name,
            async_client=async_client,  # type: ignore[call-arg]
            managed_client=managed_client,
            named_vectors=named_vectors,  # type: ignore[call-arg]
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
        collection: CollectionAsync = self.async_client.collections.get(self.collection_name)
        response = await collection.data.insert_many(records)
        return [str(v) for _, v in response.uuids.items()]

    @override
    async def _inner_get(self, keys: Sequence[TKey], **kwargs: Any) -> OneOrMany[Any] | None:
        collection: CollectionAsync = self.async_client.collections.get(self.collection_name)
        result = await collection.query.fetch_objects(
            filters=Filter.any_of([Filter.by_id().equal(key) for key in keys]),
            include_vector=kwargs.get("include_vectors", False),
        )

        return result.objects

    @override
    async def _inner_delete(self, keys: Sequence[TKey], **kwargs: Any) -> None:
        collection: CollectionAsync = self.async_client.collections.get(self.collection_name)
        await collection.data.delete_many(where=Filter.any_of([Filter.by_id().equal(key) for key in keys]))

    @override
    async def _inner_search(
        self,
        options: VectorSearchOptions,
        search_text: str | None = None,
        vectorizable_text: str | None = None,
        vector: list[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        vector_field = self.data_model_definition.try_get_vector_field(options.vector_field_name)
        collection: CollectionAsync = self.async_client.collections.get(self.collection_name)
        args = {
            "filters": create_filter_from_vector_search_filters(options.filter),
            "include_vector": options.include_vectors,
            "limit": options.top,
            "offset": options.skip,
        }
        if search_text:
            results = await self._inner_vector_text_search(collection, search_text, args)
        elif vectorizable_text:
            results = await self._inner_vectorizable_text_search(collection, vectorizable_text, vector_field, args)
        elif vector:
            results = await self._inner_vectorized_search(collection, vector, vector_field, args)
        else:
            raise VectorSearchExecutionException("No search criteria provided.")

        return KernelSearchResults(
            results=self._get_vector_search_results_from_results(results.objects), total_count=len(results.objects)
        )

    async def _inner_vector_text_search(
        self, collection: CollectionAsync, search_text: str, args: dict[str, Any]
    ) -> Any:
        try:
            return await collection.query.bm25(
                query=search_text,
                return_metadata=MetadataQuery(score=True),
                **args,
            )
        except Exception as ex:
            raise VectorSearchExecutionException(f"Failed searching using a text: {ex}") from ex

    async def _inner_vectorizable_text_search(
        self,
        collection: CollectionAsync,
        vectorizable_text: str,
        vector_field: VectorStoreRecordVectorField | None,
        args: dict[str, Any],
    ) -> Any:
        if self.named_vectors and not vector_field:
            raise VectorSearchExecutionException(
                "Vectorizable text search requires a vector field to be specified in the options."
            )
        try:
            return await collection.query.near_text(
                query=vectorizable_text,
                target_vector=vector_field.name if self.named_vectors and vector_field else None,
                return_metadata=MetadataQuery(distance=True),
                **args,
            )
        except Exception as ex:
            logger.error(
                f"Failed searching using a vectorizable text: {ex}. "
                "This is probably due to not having setup Weaviant with a vectorizer, the default config for a "
                "collection does not include a vectorizer, you would have to supply a custom set of arguments"
                "to the create_collection method to include a vectorizer."
                "Alternatively you could use a existing collection that has a vectorizer setup."
                "See also: https://weaviate.io/developers/weaviate/manage-data/collections#create-a-collection"
            )
            raise VectorSearchExecutionException(f"Failed searching using a vectorizable text: {ex}") from ex

    async def _inner_vectorized_search(
        self,
        collection: CollectionAsync,
        vector: list[float | int],
        vector_field: VectorStoreRecordVectorField | None,
        args: dict[str, Any],
    ) -> Any:
        if self.named_vectors and not vector_field:
            raise VectorSearchExecutionException(
                "Vectorizable text search requires a vector field to be specified in the options."
            )
        try:
            return await collection.query.near_vector(
                near_vector=vector,
                target_vector=vector_field.name if self.named_vectors and vector_field else None,
                return_metadata=MetadataQuery(distance=True),
                **args,
            )
        except WeaviateClosedClientError as ex:
            raise VectorSearchExecutionException(
                "Client is closed, please use the context manager or self.async_client.connect."
            ) from ex
        except Exception as ex:
            raise VectorSearchExecutionException(f"Failed searching using a vector: {ex}") from ex

    def _get_record_from_result(self, result: Any) -> Any:
        """Get the record from the returned search result."""
        return result

    def _get_score_from_result(self, result: Any) -> float | None:
        if result.metadata and result.metadata.score is not None:
            return result.metadata.score
        if result.metadata and result.metadata.distance is not None:
            return result.metadata.distance
        return None

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
                record, self.data_model_definition, self.named_vectors
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
                record, self.data_model_definition, self.named_vectors
            )

            records_in_dict.append(properties | key | vectors)

        return records_in_dict

    @override
    async def create_collection(self, **kwargs) -> None:
        """Create the collection in Weaviate.

        Args:
            **kwargs: Additional keyword arguments, when any kwargs are supplied they are passed
                straight to the Weaviate client.collections.create method.
                Make sure to check the arguments of that method for the specifications.
        """
        if not self.named_vectors and len(self.data_model_definition.vector_field_names) != 1:
            raise VectorStoreOperationException(
                "Named vectors must be enabled if there is not exactly one vector field in the data model definition."
            )
        if kwargs:
            try:
                await self.async_client.collections.create(**kwargs)
            except WeaviateClosedClientError as ex:
                raise VectorStoreOperationException(
                    "Client is closed, please use the context manager or self.async_client.connect."
                ) from ex
            except Exception as ex:
                raise VectorStoreOperationException(f"Failed to create collection: {ex}") from ex
        try:
            await self.async_client.collections.create(
                name=self.collection_name,
                properties=data_model_definition_to_weaviate_properties(self.data_model_definition),
                vector_index_config=to_weaviate_vector_index_config(
                    self.data_model_definition.fields[self.data_model_definition.vector_field_names[0]]
                )
                if not self.named_vectors
                else None,
                vectorizer_config=data_model_definition_to_weaviate_named_vectors(self.data_model_definition)
                if self.named_vectors
                else None,
            )
        except WeaviateClosedClientError as ex:
            raise VectorStoreOperationException(
                "Client is closed, please use the context manager or self.async_client.connect."
            ) from ex
        except Exception as ex:
            raise VectorStoreOperationException(f"Failed to create collection: {ex}") from ex

    @override
    async def does_collection_exist(self, **kwargs) -> bool:
        """Check if the collection exists in Weaviate.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            bool: Whether the collection exists.
        """
        try:
            return await self.async_client.collections.exists(self.collection_name)
        except WeaviateClosedClientError as ex:
            raise VectorStoreOperationException(
                "Client is closed, please use the context manager or self.async_client.connect."
            ) from ex
        except Exception as ex:
            raise VectorStoreOperationException(f"Failed to check if collection exists: {ex}") from ex

    @override
    async def delete_collection(self, **kwargs) -> None:
        """Delete the collection in Weaviate.

        Args:
            **kwargs: Additional keyword arguments.
        """
        try:
            await self.async_client.collections.delete(self.collection_name)
        except WeaviateClosedClientError as ex:
            raise VectorStoreOperationException(
                "Client is closed, please use the context manager or self.async_client.connect."
            ) from ex
        except Exception as ex:
            raise VectorStoreOperationException(f"Failed to delete collection: {ex}") from ex

    @override
    async def __aenter__(self) -> "WeaviateCollection":
        """Enter the context manager."""
        await self.async_client.connect()
        return self

    @override
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager."""
        if self.managed_client:
            await self.async_client.close()

    def _validate_data_model(self):
        super()._validate_data_model()
        if self.named_vectors and len(self.data_model_definition.vector_field_names) > 1:
            raise VectorStoreModelValidationError(
                "Named vectors must be enabled if there are more then 1 vector fields in the data model definition."
            )
