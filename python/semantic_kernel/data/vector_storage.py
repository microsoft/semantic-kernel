# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from abc import abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any, ClassVar, Generic, TypeVar, overload

from pydantic import BaseModel, Field, model_validator
from pydantic.dataclasses import dataclass

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.data.record_definition import (
    SerializeMethodProtocol,
    VectorStoreRecordDefinition,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.exceptions import (
    VectorStoreModelDeserializationException,
    VectorStoreModelException,
    VectorStoreModelSerializationException,
    VectorStoreModelValidationError,
    VectorStoreOperationException,
)
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.kernel_types import OneOrMany, OptionalOneOrMany
from semantic_kernel.utils.feature_stage_decorator import release_candidate

if sys.version_info >= (3, 11):
    from typing import Self  # pragma: no cover
else:
    from typing_extensions import Self  # pragma: no cover


TModel = TypeVar("TModel", bound=object)
TKey = TypeVar("TKey")
_T = TypeVar("_T", bound="VectorStoreRecordHandler")

logger = logging.getLogger(__name__)


def _get_collection_name_from_model(
    data_model_type: type[TModel],
    data_model_definition: VectorStoreRecordDefinition | None = None,
) -> str | None:
    """Get the collection name from the data model type or definition."""
    if data_model_type and not data_model_definition:
        data_model_definition = getattr(data_model_type, "__kernel_vectorstoremodel_definition__", None)
    if data_model_definition and data_model_definition.collection_name:
        return data_model_definition.collection_name
    return None


@dataclass
class OrderBy:
    """Order by class."""

    field: str
    ascending: bool = Field(default=True)


@dataclass
class GetFilteredRecordOptions:
    """Options for filtering records."""

    top: int = 10
    skip: int = 0
    order_by: OptionalOneOrMany[OrderBy] = None


@release_candidate
class VectorStoreRecordHandler(KernelBaseModel, Generic[TKey, TModel]):
    """Vector Store Record Handler class.

    This class is used to serialize and deserialize records to and from a vector store.
    As well as validating the data model against the vector store.
    It is subclassed by VectorStoreRecordCollection and VectorSearchBase.
    """

    data_model_type: type[TModel]
    data_model_definition: VectorStoreRecordDefinition
    supported_key_types: ClassVar[set[str] | None] = None
    supported_vector_types: ClassVar[set[str] | None] = None
    embedding_generator: EmbeddingGeneratorBase | None = None

    @property
    def _key_field_name(self) -> str:
        return self.data_model_definition.key_field_name

    @property
    def _key_field_storage_property_name(self) -> str:
        return self.data_model_definition.key_field.storage_property_name or self.data_model_definition.key_field_name

    @property
    def _container_mode(self) -> bool:
        return self.data_model_definition.container_mode

    @model_validator(mode="before")
    @classmethod
    def _ensure_data_model_definition(cls: type[_T], data: Any) -> dict[str, Any]:
        """Ensure there is a  data model definition, if it isn't passed, try to get it from the data model type."""
        if isinstance(data, dict) and not data.get("data_model_definition"):
            data["data_model_definition"] = getattr(
                data["data_model_type"], "__kernel_vectorstoremodel_definition__", None
            )
        return data

    def model_post_init(self, __context: object | None = None):
        """Post init function that sets the key field and container mode values, and validates the datamodel."""
        self._validate_data_model()

    def _validate_data_model(self):
        """Internal function that can be overloaded by child classes to validate datatypes, etc.

        This should take the VectorStoreRecordDefinition from the item_type and validate it against the store.

        Checks can include, allowed naming of parameters, allowed data types, allowed vector dimensions.

        Default checks are that the key field is in the allowed key types and the vector fields
        are in the allowed vector types.

        Raises:
            VectorStoreModelValidationError: If the key field is not in the allowed key types.
            VectorStoreModelValidationError: If the vector fields are not in the allowed vector types.

        """
        if (
            self.supported_key_types
            and self.data_model_definition.key_field.property_type
            and self.data_model_definition.key_field.property_type not in self.supported_key_types
        ):
            raise VectorStoreModelValidationError(
                f"Key field must be one of {self.supported_key_types}, "
                f"got {self.data_model_definition.key_field.property_type}"
            )
        if not self.supported_vector_types:
            return
        for field in self.data_model_definition.vector_fields:
            if field.property_type and field.property_type not in self.supported_vector_types:
                raise VectorStoreModelValidationError(
                    f"Vector field {field.name} must be one of {self.supported_vector_types}, got {field.property_type}"
                )

    @abstractmethod
    def _serialize_dicts_to_store_models(self, records: Sequence[dict[str, Any]], **kwargs: Any) -> Sequence[Any]:
        """Serialize a list of dicts of the data to the store model.

        This method should be overridden by the child class to convert the dict to the store model.
        """
        ...  # pragma: no cover

    @abstractmethod
    def _deserialize_store_models_to_dicts(self, records: Sequence[Any], **kwargs: Any) -> Sequence[dict[str, Any]]:
        """Deserialize the store models to a list of dicts.

        This method should be overridden by the child class to convert the store model to a list of dicts.
        """
        ...  # pragma: no cover

    # region Serialization methods

    def serialize(self, records: OneOrMany[TModel], **kwargs: Any) -> OneOrMany[Any]:
        """Serialize the data model to the store model.

        This method follows the following steps:
        1. Check if the data model has a serialize method.
            Use that method to serialize and return the result.
        2. Serialize the records into a dict, using the data model specific method.
        3. Convert the dict to the store model, using the store specific method.

        If overriding this method, make sure to first try to serialize the data model to the store model,
        before doing the store specific version,
        the user supplied version should have precedence.

        Raises:
            VectorStoreModelSerializationException: If an error occurs during serialization.

        """
        try:
            if serialized := self._serialize_data_model_to_store_model(records):
                return serialized

            if isinstance(records, Sequence):
                dict_records = [self._serialize_data_model_to_dict(rec) for rec in records]
                return self._serialize_dicts_to_store_models(dict_records, **kwargs)  # type: ignore

            dict_records = self._serialize_data_model_to_dict(records)  # type: ignore
            if isinstance(dict_records, Sequence):
                # most likely this is a container, so we return all records as a list
                # can also be a single record, but the to_dict returns a list
                # hence we will treat it as a container.
                return self._serialize_dicts_to_store_models(dict_records, **kwargs)  # type: ignore
            # this case is single record in, single record out
            return self._serialize_dicts_to_store_models([dict_records], **kwargs)[0]
        except VectorStoreModelSerializationException:
            raise  # pragma: no cover
        except Exception as exc:
            raise VectorStoreModelSerializationException(f"Error serializing records: {exc}") from exc

    def _serialize_data_model_to_store_model(self, record: OneOrMany[TModel], **kwargs: Any) -> OneOrMany[Any] | None:
        """Serialize the data model to the store model.

        This works when the data model has supplied a serialize method, specific to a data source.
        This is a method called 'serialize()' on the data model or part of the vector store record definition.

        The developer is responsible for correctly serializing for the specific data source.
        """
        if isinstance(record, Sequence):
            result = [self._serialize_data_model_to_store_model(rec, **kwargs) for rec in record]
            if not all(result):
                return None
            return result
        if self.data_model_definition.serialize:
            return self.data_model_definition.serialize(record, **kwargs)
        if isinstance(record, SerializeMethodProtocol):
            return record.serialize(**kwargs)
        return None

    def _serialize_data_model_to_dict(self, record: TModel, **kwargs: Any) -> OneOrMany[dict[str, Any]]:
        """This function is used if no serialize method is found on the data model.

        This will generally serialize the data model to a dict, should not be overridden by child classes.

        The output of this should be passed to the serialize_dict_to_store_model method.
        """
        if self.data_model_definition.to_dict:
            return self.data_model_definition.to_dict(record, **kwargs)
        if isinstance(record, BaseModel):
            return record.model_dump()

        store_model = {}
        for field in self.data_model_definition.fields:
            store_model[field.storage_property_name or field.name] = (
                record.get(field.name, None) if isinstance(record, Mapping) else getattr(record, field.name)
            )
        return store_model

    # region Deserialization methods

    def deserialize(self, records: OneOrMany[Any | dict[str, Any]], **kwargs: Any) -> OneOrMany[TModel] | None:
        """Deserialize the store model to the data model.

        This method follows the following steps:
        1. Check if the data model has a deserialize method.
            Use that method to deserialize and return the result.
        2. Deserialize the store model to a dict, using the store specific method.
        3. Convert the dict to the data model, using the data model specific method.

        Raises:
            VectorStoreModelDeserializationException: If an error occurs during deserialization.
        """
        try:
            if not records:
                return None
            if deserialized := self._deserialize_store_model_to_data_model(records, **kwargs):
                return deserialized

            if isinstance(records, Sequence):
                dict_records = self._deserialize_store_models_to_dicts(records, **kwargs)
                return (
                    self._deserialize_dict_to_data_model(dict_records, **kwargs)
                    if self._container_mode
                    else [self._deserialize_dict_to_data_model(rec, **kwargs) for rec in dict_records]
                )

            dict_record = self._deserialize_store_models_to_dicts([records], **kwargs)[0]
            # regardless of mode, only 1 object is returned.
            return self._deserialize_dict_to_data_model(dict_record, **kwargs)
        except VectorStoreModelDeserializationException:
            raise  # pragma: no cover
        except Exception as exc:
            raise VectorStoreModelDeserializationException(f"Error deserializing records: {exc}") from exc

    def _deserialize_store_model_to_data_model(self, record: OneOrMany[Any], **kwargs: Any) -> OneOrMany[TModel] | None:
        """Deserialize the store model to the data model.

        This works when the data model has supplied a deserialize method, specific to a data source.
        This uses a method called 'deserialize()' on the data model or part of the vector store record definition.

        The developer is responsible for correctly deserializing for the specific data source.
        """
        if self.data_model_definition.deserialize:
            if isinstance(record, Sequence):
                return self.data_model_definition.deserialize(record, **kwargs)
            return self.data_model_definition.deserialize([record], **kwargs)
        if func := getattr(self.data_model_type, "deserialize", None):
            if isinstance(record, Sequence):
                return [func(rec, **kwargs) for rec in record]
            return func(record, **kwargs)
        return None

    def _deserialize_dict_to_data_model(self, record: OneOrMany[dict[str, Any]], **kwargs: Any) -> TModel:
        """This function is used if no deserialize method is found on the data model.

        This method is the second step and will deserialize a dict to the data model,
        should not be overridden by child classes.

        The input of this should come from the _deserialized_store_model_to_dict function.
        """
        if self.data_model_definition.from_dict:
            if isinstance(record, Sequence):
                return self.data_model_definition.from_dict(record, **kwargs)
            ret = self.data_model_definition.from_dict([record], **kwargs)
            return ret if self._container_mode else ret[0]
        if isinstance(record, Sequence):
            if len(record) > 1:
                raise VectorStoreModelDeserializationException(
                    "Cannot deserialize multiple records to a single record unless you are using a container."
                )
            record = record[0]
        if func := getattr(self.data_model_type, "from_dict", None):
            return func(record)
        if issubclass(self.data_model_type, BaseModel):
            for field in self.data_model_definition.fields:
                if field.storage_property_name and field.storage_property_name in record:
                    record[field.name] = record.pop(field.storage_property_name)
            return self.data_model_type.model_validate(record)  # type: ignore
        data_model_dict: dict[str, Any] = {}
        for field in self.data_model_definition.fields:
            value = record.get(field.storage_property_name or field.name, None)
            if isinstance(field, VectorStoreRecordVectorField) and not kwargs.get("include_vectors"):
                continue
            data_model_dict[field.name] = value
        if self.data_model_type is dict:
            return data_model_dict  # type: ignore
        return self.data_model_type(**data_model_dict)

    # region: add_vector_to_records

    @release_candidate
    async def _add_vectors_to_records(
        self,
        records: OneOrMany[dict[str, Any]],
        **kwargs,
    ) -> OneOrMany[dict[str, Any]]:
        """Vectorize the vector record.

        This function can be passed to upsert or upsert batch of a VectorStoreRecordCollection.

        Loops through the fields of the data model definition,
        looks at data fields, if they have a vector field,
        looks up that vector field and checks if is a local embedding.

        If so adds that to a list of embeddings to make.

        Finally calls Kernel add_embedding_to_object with the list of embeddings to make.

        Optional arguments are passed onto the Kernel add_embedding_to_object call.
        """
        # dict of embedding_field.name and tuple of record, settings, field_name
        embeddings_to_make: list[tuple[str, int, EmbeddingGeneratorBase]] = []

        for field in self.data_model_definition.vector_fields:
            embedding_generator = field.embedding_generator or self.embedding_generator
            if not embedding_generator:
                continue
            embeddings_to_make.append((
                field.storage_property_name or field.name,
                field.dimensions,
                embedding_generator,
            ))

        for field_name, dimensions, embedder in embeddings_to_make:
            await self._add_embedding_to_object(
                inputs=records,
                field_name=field_name,
                dimensions=dimensions,
                embedding_generator=embedder,
                container_mode=self.data_model_definition.container_mode,
                **kwargs,
            )
        return records

    async def _add_embedding_to_object(
        self,
        inputs: OneOrMany[Any],
        field_name: str,
        dimensions: int,
        embedding_generator: EmbeddingGeneratorBase,
        container_mode: bool = False,
        **kwargs: Any,
    ):
        """Gather all fields to embed, batch the embedding generation and store."""
        contents: list[Any] = []
        dict_like = (getter := getattr(inputs, "get", False)) and callable(getter)
        list_of_dicts: bool = False
        if container_mode:
            contents = inputs[field_name].tolist()  # type: ignore
        elif isinstance(inputs, list):
            list_of_dicts = (getter := getattr(inputs[0], "get", False)) and callable(getter)
            for record in inputs:
                if list_of_dicts:
                    contents.append(record.get(field_name))  # type: ignore
                else:
                    contents.append(getattr(record, field_name))
        else:
            if dict_like:
                contents.append(inputs.get(field_name))  # type: ignore
            else:
                contents.append(getattr(inputs, field_name))

        vectors = await embedding_generator.generate_raw_embeddings(
            texts=contents, settings=PromptExecutionSettings(dimensions=dimensions), **kwargs
        )  # type: ignore
        if vectors is None:
            raise VectorStoreOperationException("No vectors were generated.")
        if container_mode:
            inputs[field_name] = vectors  # type: ignore
            return
        if isinstance(inputs, list):
            for record, vector in zip(inputs, vectors):
                if list_of_dicts:
                    record[field_name] = vector  # type: ignore
                else:
                    setattr(record, field_name, vector)
            return
        if dict_like:
            inputs[field_name] = vectors[0]  # type: ignore
            return
        setattr(inputs, field_name, vectors[0])


# region: VectorStoreRecordCollection


@release_candidate
class VectorStoreRecordCollection(VectorStoreRecordHandler[TKey, TModel], Generic[TKey, TModel]):
    """Base class for a vector store record collection."""

    collection_name: str = ""
    managed_client: bool = True

    @model_validator(mode="before")
    @classmethod
    def _ensure_collection_name(cls: type[_T], data: Any) -> dict[str, Any]:
        """Ensure there is a collection name, if it isn't passed, try to get it from the data model type."""
        if (
            isinstance(data, dict)
            and not data.get("collection_name")
            and (
                collection_name := _get_collection_name_from_model(
                    data["data_model_type"], data.get("data_model_definition")
                )
            )
        ):
            data["collection_name"] = collection_name
        return data

    async def __aenter__(self) -> Self:
        """Enter the context manager."""
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager.

        Should be overridden by subclasses, if necessary.

        If the client is passed in the constructor, it should not be closed,
        in that case the managed_client should be set to False.

        If the store supplied the managed client, it is responsible for closing it,
        and it should not be closed here and so managed_client should be False.

        Some services use two clients, one for the store and one for the collection,
        in that case, the collection client should be closed here,
        but the store client should only be closed when it is created in the collection.
        A additional flag might be needed for that.
        """
        pass

    @abstractmethod
    async def _inner_upsert(
        self,
        records: Sequence[Any],
        **kwargs: Any,
    ) -> Sequence[TKey]:
        """Upsert the records, this should be overridden by the child class.

        Args:
            records: The records, the format is specific to the store.
            **kwargs (Any): Additional arguments, to be passed to the store.

        Returns:
            The keys of the upserted records.

        Raises:
            Exception: If an error occurs during the upsert.
                There is no need to catch and parse exceptions in the inner functions,
                they are handled by the public methods.
                The only exception is raises exceptions yourself, such as a ValueError.
                This is then caught and turned into the relevant exception by the public method.
                This setup promotes a limited depth of the stack trace.

        """
        ...  # pragma: no cover

    @abstractmethod
    async def _inner_get(
        self,
        keys: Sequence[TKey] | None = None,
        options: GetFilteredRecordOptions | None = None,
        **kwargs: Any,
    ) -> OneOrMany[Any] | None:
        """Get the records, this should be overridden by the child class.

        Args:
            keys: The keys to get.
            options: the options to use for the get.
            **kwargs: Additional arguments.

        Returns:
            The records from the store, not deserialized.

        Raises:
            Exception: If an error occurs during the upsert.
                There is no need to catch and parse exceptions in the inner functions,
                they are handled by the public methods.
                The only exception is raises exceptions yourself, such as a ValueError.
                This is then caught and turned into the relevant exception by the public method.
                This setup promotes a limited depth of the stack trace.
        """
        ...  # pragma: no cover

    @abstractmethod
    async def _inner_delete(self, keys: Sequence[TKey], **kwargs: Any) -> None:
        """Delete the records, this should be overridden by the child class.

        Args:
            keys: The keys.
            **kwargs: Additional arguments.

        Raises:
            Exception: If an error occurs during the upsert.
                There is no need to catch and parse exceptions in the inner functions,
                they are handled by the public methods.
                The only exception is raises exceptions yourself, such as a ValueError.
                This is then caught and turned into the relevant exception by the public method.
                This setup promotes a limited depth of the stack trace.
        """
        ...  # pragma: no cover

    async def create_collection_if_not_exists(self, **kwargs: Any) -> bool:
        """Create the collection in the service if it does not exists.

        First uses does_collection_exist to check if it exists, if it does returns False.
        Otherwise, creates the collection and returns True.

        """
        if await self.does_collection_exist(**kwargs):
            return False
        await self.create_collection(**kwargs)
        return True

    @abstractmethod
    async def create_collection(self, **kwargs: Any) -> None:
        """Create the collection in the service.

        This should be overridden by the child class.

        Raises:
            Make sure the implementation of this function raises relevant exceptions with good descriptions.
            This is different then the `_inner_x` methods, as this is a public method.

        """
        ...  # pragma: no cover

    @abstractmethod
    async def does_collection_exist(self, **kwargs: Any) -> bool:
        """Check if the collection exists.

        This should be overridden by the child class.

        Raises:
            Make sure the implementation of this function raises relevant exceptions with good descriptions.
            This is different then the `_inner_x` methods, as this is a public method.
        """
        ...  # pragma: no cover

    @abstractmethod
    async def delete_collection(self, **kwargs: Any) -> None:
        """Delete the collection.

        This should be overridden by the child class.

        Raises:
            Make sure the implementation of this function raises relevant exceptions with good descriptions.
            This is different then the `_inner_x` methods, as this is a public method.
        """
        ...  # pragma: no cover

    # region Public Methods

    async def upsert(
        self,
        records: OneOrMany[TModel],
        **kwargs,
    ) -> OneOrMany[TKey]:
        """Upsert one or more records.

        If the key of the record already exists, the existing record will be updated.
        If the key does not exist, a new record will be created.

        Args:
            records: The records to upsert, can be a single record, a list of records, or a single container.
                If a single record is passed, a single key is returned, instead of a list of keys.
            **kwargs: Additional arguments.

        Returns:
            OneOrMany[TKey]: The keys of the upserted records.

        Raises:
            VectorStoreModelSerializationException: If an error occurs during serialization.
            VectorStoreOperationException: If an error occurs during upserting.
        """
        batch = True
        if not isinstance(records, list) and not self._container_mode:
            batch = False
        if records is None:
            raise VectorStoreOperationException("Either record or records must be provided.")

        try:
            data = self.serialize(records)
        # the serialize method will parse any exception into a VectorStoreModelSerializationException
        except VectorStoreModelSerializationException:
            raise

        try:
            # fix this!
            data = await self._add_vectors_to_records(data)
        except (VectorStoreModelException, VectorStoreOperationException):
            raise
        except Exception as exc:
            raise VectorStoreOperationException(
                "Exception occurred while trying to add the vectors to the records."
            ) from exc
        try:
            results = await self._inner_upsert(data if isinstance(data, list) else [data], **kwargs)  # type: ignore
        except Exception as exc:
            raise VectorStoreOperationException(f"Error upserting record(s): {exc}") from exc
        if batch or self._container_mode:
            return results
        return results[0]

    @overload
    async def get(
        self,
        top: int = ...,
        skip: int = ...,
        order_by: OptionalOneOrMany[OrderBy | dict[str, Any] | list[dict[str, Any]]] = None,
        include_vectors: bool = False,
        **kwargs: Any,
    ) -> Sequence[TModel] | None:
        """Get records based on the ordering and selection criteria.

        Args:
            include_vectors: Include the vectors in the response. Default is True.
                Some vector stores do not support retrieving without vectors, even when set to false.
                Some vector stores have specific parameters to control that behavior, when
                that parameter is set, include_vectors is ignored.
            top: The number of records to return.
                Only used if keys are not provided.
            skip: The number of records to skip.
                Only used if keys are not provided.
            order_by: The order by clause, this is a list of dicts with the field name and ascending flag,
                (default is True, which means ascending).
                Only used if keys are not provided.
                example: {"field": "hotel_id", "ascending": True}
            **kwargs: Additional arguments.

        Returns:
            The records, either a list of TModel or the container type.

        Raises:
            VectorStoreOperationException: If an error occurs during the get.
            VectorStoreModelDeserializationException: If an error occurs during deserialization.
        """
        ...

    @overload
    async def get(
        self,
        key: TKey = ...,
        include_vectors: bool = False,
        **kwargs: Any,
    ) -> TModel | None:
        """Get a record if it exists.

        Args:
            key: The key to get.
            include_vectors: Include the vectors in the response. Default is True.
                Some vector stores do not support retrieving without vectors, even when set to false.
                Some vector stores have specific parameters to control that behavior, when
                that parameter is set, include_vectors is ignored.
            **kwargs: Additional arguments.

        Returns:
            The records, either a list of TModel or the container type.

        Raises:
            VectorStoreOperationException: If an error occurs during the get.
            VectorStoreModelDeserializationException: If an error occurs during deserialization.
        """
        ...

    @overload
    async def get(
        self,
        keys: Sequence[TKey] = ...,
        include_vectors: bool = False,
        **kwargs: Any,
    ) -> OneOrMany[TModel] | None:
        """Get a batch of records whose keys exist in the collection, i.e. keys that do not exist are ignored.

        Args:
            keys: The keys to get, if keys are provided, key is ignored.
            include_vectors: Include the vectors in the response. Default is True.
                Some vector stores do not support retrieving without vectors, even when set to false.
                Some vector stores have specific parameters to control that behavior, when
                that parameter is set, include_vectors is ignored.
            **kwargs: Additional arguments.

        Returns:
            The records, either a list of TModel or the container type.

        Raises:
            VectorStoreOperationException: If an error occurs during the get.
            VectorStoreModelDeserializationException: If an error occurs during deserialization.
        """
        ...

    async def get(
        self,
        key=None,
        keys=None,
        include_vectors=False,
        **kwargs,
    ):
        """Get a batch of records whose keys exist in the collection, i.e. keys that do not exist are ignored.

        Args:
            key: The key to get.
            keys: The keys to get, if keys are provided, key is ignored.
            include_vectors: Include the vectors in the response. Default is True.
                Some vector stores do not support retrieving without vectors, even when set to false.
                Some vector stores have specific parameters to control that behavior, when
                that parameter is set, include_vectors is ignored.
            top: The number of records to return.
                Only used if keys are not provided.
            skip: The number of records to skip.
                Only used if keys are not provided.
            order_by: The order by clause, this is a list of dicts with the field name and ascending flag,
                (default is True, which means ascending).
                Only used if keys are not provided.
            **kwargs: Additional arguments.

        Returns:
            The records, either a list of TModel or the container type.

        Raises:
            VectorStoreOperationException: If an error occurs during the get.
            VectorStoreModelDeserializationException: If an error occurs during deserialization.
        """
        batch = True
        options = None
        if not keys and key:
            if not isinstance(key, list):
                keys = [key]
                batch = False
            else:
                keys = key
        if not keys:
            if kwargs:
                try:
                    options = GetFilteredRecordOptions(**kwargs)
                except Exception as exc:
                    raise VectorStoreOperationException(f"Error creating options: {exc}") from exc
            else:
                raise VectorStoreOperationException("Either key, keys or options must be provided.")
        try:
            records = await self._inner_get(keys, include_vectors=include_vectors, options=options, **kwargs)
        except Exception as exc:
            raise VectorStoreOperationException(f"Error getting record(s): {exc}") from exc

        if not records:
            return None

        try:
            model_records = self.deserialize(
                records if batch else records[0], include_vectors=include_vectors, **kwargs
            )
        # the deserialize method will parse any exception into a VectorStoreModelDeserializationException
        except VectorStoreModelDeserializationException:
            raise

        # there are many code paths within the deserialize method, some supplied by the developer,
        # and so depending on what is used,
        # it might return a sequence, so we just return the first element,
        # there should never be multiple elements (this is not a batch get),
        # hence a raise if there are.
        if batch:
            return model_records
        if not isinstance(model_records, Sequence):
            return model_records
        if len(model_records) == 1:
            return model_records[0]
        raise VectorStoreModelDeserializationException(
            f"Error deserializing record, multiple records returned: {model_records}"
        )

    async def delete(self, keys: OneOrMany[TKey], **kwargs):
        """Delete one or more records by key.

        An exception will be raised at the end if any record does not exist.

        Args:
            keys: The key or keys to be deleted.
            **kwargs: Additional arguments.
        Exceptions:
            VectorStoreOperationException: If an error occurs during deletion or a record does not exist.
        """
        if not isinstance(keys, list):
            keys = [keys]  # type: ignore
        try:
            await self._inner_delete(keys, **kwargs)  # type: ignore
        except Exception as exc:
            raise VectorStoreOperationException(f"Error deleting record(s): {exc}") from exc


@release_candidate
class VectorStore(KernelBaseModel):
    """Base class for vector stores."""

    managed_client: bool = True
    embedding_generator: EmbeddingGeneratorBase | None = None

    @abstractmethod
    def get_collection(
        self,
        data_model_type: type[TModel],
        *,
        data_model_definition: VectorStoreRecordDefinition | None = None,
        collection_name: str | None = None,
        embedding_generator: EmbeddingGeneratorBase | None = None,
        **kwargs: Any,
    ) -> "VectorStoreRecordCollection":
        """Get a vector store record collection instance tied to this store.

        Args:
            data_model_type: The type of the data model.
            data_model_definition: The data model definition.
            collection_name: The name of the collection.
            embedding_generator: The embedding generator to use.
            **kwargs: Additional arguments.

        Returns:
            A vector store record collection instance tied to this store.

        """
        ...  # pragma: no cover

    @abstractmethod
    async def list_collection_names(self, **kwargs) -> Sequence[str]:
        """Get the names of all collections."""
        ...  # pragma: no cover

    async def does_collection_exist(self, collection_name: str) -> bool:
        """Check if a collection exists.

        This is a wrapper around the get_collection method of a collection,
        to check if the collection exists.
        """
        try:
            data_model = VectorStoreRecordDefinition(fields=[VectorStoreRecordKeyField(name="id")])
            collection = self.get_collection(
                data_model_type=dict, data_model_definition=data_model, collection_name=collection_name
            )
            return await collection.does_collection_exist()
        except VectorStoreOperationException:
            return False

    async def delete_collection(self, collection_name: str) -> None:
        """Delete a collection.

        This is a wrapper around the get_collection method of a collection,
        to delete the collection.
        """
        try:
            data_model = VectorStoreRecordDefinition(fields=[VectorStoreRecordKeyField(name="id")])
            collection = self.get_collection(
                data_model_type=dict, data_model_definition=data_model, collection_name=collection_name
            )
            await collection.delete_collection()
        except VectorStoreOperationException:
            pass

    async def __aenter__(self) -> Self:
        """Enter the context manager."""
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager.

        Should be overridden by subclasses, if necessary.

        If the client is passed in the constructor, it should not be closed,
        in that case the managed_client should be set to False.
        """
        pass  # pragma: no cover
