# Copyright (c) Microsoft. All rights reserved.

import asyncio
import contextlib
import logging
from abc import abstractmethod
from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Any, ClassVar, Generic, TypeVar

from pydantic import BaseModel, model_validator

from semantic_kernel.data.record_definition.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.record_definition.vector_store_model_protocols import (
    SerializeMethodProtocol,
    ToDictMethodProtocol,
)
from semantic_kernel.exceptions import (
    VectorStoreModelDeserializationException,
    VectorStoreModelSerializationException,
    VectorStoreModelValidationError,
    VectorStoreOperationException,
)
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.kernel_types import OneOrMany
from semantic_kernel.utils.experimental_decorator import experimental_class

TModel = TypeVar("TModel", bound=object)
TKey = TypeVar("TKey")
_T = TypeVar("_T", bound="VectorStoreRecordCollection")

logger = logging.getLogger(__name__)


@experimental_class
class VectorStoreRecordCollection(KernelBaseModel, Generic[TKey, TModel]):
    """Base class for a vector store record collection."""

    collection_name: str
    data_model_type: type[TModel]
    data_model_definition: VectorStoreRecordDefinition
    supported_key_types: ClassVar[list[str] | None] = None
    supported_vector_types: ClassVar[list[str] | None] = None
    managed_client: bool = True

    @property
    def _container_mode(self) -> bool:
        return self.data_model_definition.container_mode

    @property
    def _key_field_name(self) -> str:
        return self.data_model_definition.key_field_name

    @model_validator(mode="before")
    @classmethod
    def _ensure_data_model_definition(cls: type[_T], data: dict[str, Any]) -> dict[str, Any]:
        """Ensure there is a  data model definition, if it isn't passed, try to get it from the data model type."""
        if not data.get("data_model_definition"):
            data["data_model_definition"] = getattr(
                data["data_model_type"], "__kernel_vectorstoremodel_definition__", None
            )
        return data

    def model_post_init(self, __context: object | None = None):
        """Post init function that sets the key field and container mode values, and validates the datamodel."""
        self._validate_data_model()

    async def __aenter__(self) -> "VectorStoreRecordCollection":
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
    async def _inner_get(self, keys: Sequence[TKey], **kwargs: Any) -> OneOrMany[Any] | None:
        """Get the records, this should be overridden by the child class.

        Args:
            keys: The keys to get.
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
        record: TModel,
        embedding_generation_function: Callable[
            [TModel, type[TModel] | None, VectorStoreRecordDefinition | None], Awaitable[TModel]
        ]
        | None = None,
        **kwargs: Any,
    ) -> OneOrMany[TKey] | None:
        """Upsert a record.

        If the key of the record already exists, the existing record will be updated.
        If the key does not exist, a new record will be created.

        Args:
            record: The record.
            embedding_generation_function: Supply this function to generate embeddings.
                This will be called with the data model definition and the records,
                should return the records with vectors.
                This can be supplied by using the add_vector_to_records method from the VectorStoreRecordUtils.
            **kwargs: Additional arguments.

        Returns:
            The key of the upserted record or a list of keys, when a container type is used.

        Raises:
            VectorStoreModelSerializationException: If an error occurs during serialization.
            VectorStoreOperationException: If an error occurs during upserting.
        """
        if embedding_generation_function:
            record = await embedding_generation_function(record, self.data_model_type, self.data_model_definition)

        try:
            data = self.serialize(record)
        # the serialize method will parse any exception into a VectorStoreModelSerializationException
        except VectorStoreModelSerializationException:
            raise

        try:
            results = await self._inner_upsert(data if isinstance(data, Sequence) else [data], **kwargs)
        except Exception as exc:
            raise VectorStoreOperationException(f"Error upserting record: {exc}") from exc

        if self._container_mode:
            return results
        return results[0]

    async def upsert_batch(
        self,
        records: OneOrMany[TModel],
        embedding_generation_function: Callable[
            [OneOrMany[TModel], type[TModel] | None, VectorStoreRecordDefinition | None], Awaitable[OneOrMany[TModel]]
        ]
        | None = None,
        **kwargs: Any,
    ) -> Sequence[TKey]:
        """Upsert a batch of records.

        If the key of the record already exists, the existing record will be updated.
        If the key does not exist, a new record will be created.

        Args:
            records: The records to upsert, can be a list of records, or a single container.
            embedding_generation_function: Supply this function to generate embeddings.
                This will be called with the data model definition and the records,
                should return the records with vectors.
                This can be supplied by using the add_vector_to_records method from the VectorStoreRecordUtils.
            **kwargs: Additional arguments.

        Returns:
            Sequence[TKey]: The keys of the upserted records, this is always a list,
            corresponds to the input or the items in the container.

        Raises:
            VectorStoreModelSerializationException: If an error occurs during serialization.
            VectorStoreOperationException: If an error occurs during upserting.
        """
        if embedding_generation_function:
            records = await embedding_generation_function(records, self.data_model_type, self.data_model_definition)

        try:
            data = self.serialize(records)
        # the serialize method will parse any exception into a VectorStoreModelSerializationException
        except VectorStoreModelSerializationException:
            raise

        try:
            return await self._inner_upsert(data, **kwargs)  # type: ignore
        except Exception as exc:
            raise VectorStoreOperationException(f"Error upserting records: {exc}") from exc

    async def get(self, key: TKey, include_vectors: bool = True, **kwargs: Any) -> TModel | None:
        """Get a record if the key exists.

        Args:
            key: The key.
            include_vectors: Include the vectors in the response, default is True.
                Some vector stores do not support retrieving without vectors, even when set to false.
                Some vector stores have specific parameters to control that behavior, when
                that parameter is set, include_vectors is ignored.
            **kwargs: Additional arguments.

        Returns:
            TModel: The record. None if the key does not exist.

        Raises:
            VectorStoreOperationException: If an error occurs during the get.
            VectorStoreModelDeserializationException: If an error occurs during deserialization.
        """
        try:
            records = await self._inner_get([key], include_vectors=include_vectors, **kwargs)
        except Exception as exc:
            raise VectorStoreOperationException(f"Error getting record: {exc}") from exc

        if not records:
            return None

        try:
            model_records = self.deserialize(records[0], **kwargs)
        # the deserialize method will parse any exception into a VectorStoreModelDeserializationException
        except VectorStoreModelDeserializationException:
            raise

        # there are many code paths within the deserialize method, some supplied by the developer,
        # and so depending on what is used,
        # it might return a sequence, so we just return the first element,
        # there should never be multiple elements (this is not a batch get),
        # hence a raise if there are.
        if not isinstance(model_records, Sequence):
            return model_records
        if len(model_records) == 1:
            return model_records[0]
        raise VectorStoreModelDeserializationException(
            f"Error deserializing record, multiple records returned: {model_records}"
        )

    async def get_batch(
        self, keys: Sequence[TKey], include_vectors: bool = True, **kwargs: Any
    ) -> OneOrMany[TModel] | None:
        """Get a batch of records whose keys exist in the collection, i.e. keys that do not exist are ignored.

        Args:
            keys: The keys.
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
        try:
            records = await self._inner_get(keys, include_vectors=include_vectors, **kwargs)
        except Exception as exc:
            raise VectorStoreOperationException(f"Error getting records: {exc}") from exc

        if not records:
            return None

        try:
            return self.deserialize(records, keys=keys, **kwargs)
        # the deserialize method will parse any exception into a VectorStoreModelDeserializationException
        except VectorStoreModelDeserializationException:
            raise

    async def delete(self, key: TKey, **kwargs: Any) -> None:
        """Delete a record.

        Args:
            key: The key.
            **kwargs: Additional arguments.
        Exceptions:
            VectorStoreOperationException: If an error occurs during deletion or the record does not exist.
        """
        try:
            await self._inner_delete([key], **kwargs)
        except Exception as exc:
            raise VectorStoreOperationException(f"Error deleting record: {exc}") from exc

    async def delete_batch(self, keys: Sequence[TKey], **kwargs: Any) -> None:
        """Delete a batch of records.

        An exception will be raised at the end if any record does not exist.

        Args:
            keys: The keys.
            **kwargs: Additional arguments.
        Exceptions:
            VectorStoreOperationException: If an error occurs during deletion or a record does not exist.
        """
        try:
            await self._inner_delete(keys, **kwargs)
        except Exception as exc:
            raise VectorStoreOperationException(f"Error deleting records: {exc}") from exc

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
        if isinstance(record, ToDictMethodProtocol):
            return self._serialize_vectors(record.to_dict())
        if isinstance(record, BaseModel):
            return self._serialize_vectors(record.model_dump())

        store_model = {}
        for field_name in self.data_model_definition.field_names:
            value = record[field_name] if isinstance(record, Mapping) else getattr(record, field_name)
            if func := getattr(self.data_model_definition.fields[field_name], "serialize_function", None):
                value = func(value)
            store_model[field_name] = value
        return store_model

    def _serialize_vectors(self, record: dict[str, Any]) -> dict[str, Any]:
        for field in self.data_model_definition.vector_fields:
            if field.serialize_function:
                record[field.name or ""] = field.serialize_function(record[field.name or ""])
        return record

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
        include_vectors = kwargs.get("include_vectors", True)
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
            if include_vectors:
                record = self._deserialize_vector(record)
            return func(record)
        if issubclass(self.data_model_type, BaseModel):
            if include_vectors:
                record = self._deserialize_vector(record)
            return self.data_model_type.model_validate(record)  # type: ignore
        data_model_dict: dict[str, Any] = {}
        for field_name in self.data_model_definition.fields:
            if not include_vectors and field_name in self.data_model_definition.vector_field_names:
                continue
            value = record[field_name]
            if func := getattr(self.data_model_definition.fields[field_name], "deserialize_function", None):
                value = func(value)
            data_model_dict[field_name] = value
        if self.data_model_type is dict:
            return data_model_dict  # type: ignore
        return self.data_model_type(**data_model_dict)

    def _deserialize_vector(self, record: dict[str, Any]) -> dict[str, Any]:
        for field in self.data_model_definition.vector_fields:
            if field.deserialize_function:
                record[field.name or ""] = field.deserialize_function(record[field.name or ""])
        return record

    # region Internal Functions

    def __del__(self):
        """Delete the instance."""
        with contextlib.suppress(Exception):
            asyncio.get_running_loop().create_task(self.__aexit__(None, None, None))
