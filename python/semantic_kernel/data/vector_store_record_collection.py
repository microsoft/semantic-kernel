# Copyright (c) Microsoft. All rights reserved.

import asyncio
import contextlib
import logging
from abc import abstractmethod
from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Any, ClassVar, Generic, TypeVar

from pydantic import model_validator

from semantic_kernel.data.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_store_model_protocols import (
    VectorStoreModelFunctionSerdeProtocol,
    VectorStoreModelPydanticProtocol,
    VectorStoreModelToDictFromDictProtocol,
)
from semantic_kernel.exceptions.memory_connector_exceptions import (
    MemoryConnectorException,
    VectorStoreModelDeserializationException,
    VectorStoreModelSerializationException,
    VectorStoreModelValidationError,
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

    # region Overload Methods
    async def close(self):
        """Close the connection."""
        return  # pragma: no cover

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
        """
        ...  # pragma: no cover

    @abstractmethod
    async def _inner_delete(self, keys: Sequence[TKey], **kwargs: Any) -> None:
        """Delete the records, this should be overridden by the child class.

        Args:
            keys: The keys.
            **kwargs: Additional arguments.
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
        """Create the collection in the service."""
        ...  # pragma: no cover

    @abstractmethod
    async def does_collection_exist(self, **kwargs: Any) -> bool:
        """Check if the collection exists."""
        ...  # pragma: no cover

    @abstractmethod
    async def delete_collection(self, **kwargs: Any) -> None:
        """Delete the collection."""
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

        Args:
            record: The record.
            embedding_generation_function: Supply this function to generate embeddings.
                This will be called with the data model definition and the records,
                should return the records with vectors.
                This can be supplied by using the add_vector_to_records method from the VectorStoreRecordUtils.
            **kwargs: Additional arguments.

        Returns:
            The key of the upserted record or a list of keys, when a container type is used.
        """
        if embedding_generation_function:
            record = await embedding_generation_function(record, self.data_model_type, self.data_model_definition)

        try:
            data = self.serialize(record)
        except Exception as exc:
            raise MemoryConnectorException(f"Error serializing record: {exc}") from exc

        try:
            results = await self._inner_upsert(data if isinstance(data, Sequence) else [data], **kwargs)
        except Exception as exc:
            raise MemoryConnectorException(f"Error upserting record: {exc}") from exc

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
        """
        if embedding_generation_function:
            records = await embedding_generation_function(records, self.data_model_type, self.data_model_definition)

        try:
            data = self.serialize(records)
        except Exception as exc:
            raise MemoryConnectorException(f"Error serializing records: {exc}") from exc

        try:
            return await self._inner_upsert(data, **kwargs)  # type: ignore
        except Exception as exc:
            raise MemoryConnectorException(f"Error upserting records: {exc}") from exc

    async def get(self, key: TKey, include_vectors: bool = True, **kwargs: Any) -> TModel | None:
        """Get a record.

        Args:
            key: The key.
            include_vectors: Include the vectors in the response, default is True.
                Some vector stores do not support retrieving without vectors, even when set to false.
                Some vector stores have specific parameters to control that behavior, when
                that parameter is set, include_vectors is ignored.
            **kwargs: Additional arguments.

        Returns:
            TModel: The record.
        """
        try:
            records = await self._inner_get([key], include_vectors=include_vectors, **kwargs)
        except Exception as exc:
            raise MemoryConnectorException(f"Error getting record: {exc}") from exc

        if not records:
            return None

        try:
            model_records = self.deserialize(records[0], keys=[key], **kwargs)
        except Exception as exc:
            raise MemoryConnectorException(f"Error deserializing record: {exc}") from exc

        # there are many code paths within the deserialize method, some supplied by the developer,
        # and so depending on what is used,
        # it might return a sequence, so we just return the first element,
        # there should never be multiple elements (this is not a batch get),
        # hence a raise if there are.
        if not isinstance(model_records, Sequence):
            return model_records
        if len(model_records) == 1:
            return model_records[0]
        raise MemoryConnectorException(f"Error deserializing record, multiple records returned: {model_records}")

    async def get_batch(
        self, keys: Sequence[TKey], include_vectors: bool = True, **kwargs: Any
    ) -> OneOrMany[TModel] | None:
        """Get a batch of records.

        Args:
            keys: The keys.
            include_vectors: Include the vectors in the response. Default is True.
                Some vector stores do not support retrieving without vectors, even when set to false.
                Some vector stores have specific parameters to control that behavior, when
                that parameter is set, include_vectors is ignored.
            **kwargs: Additional arguments.

        Returns:
            The records, either a list of TModel or the container type.
        """
        try:
            records = await self._inner_get(keys, include_vectors=include_vectors, **kwargs)
        except Exception as exc:
            raise MemoryConnectorException(f"Error getting records: {exc}") from exc

        if not records:
            return None

        try:
            return self.deserialize(records, keys=keys, **kwargs)
        except Exception as exc:
            raise MemoryConnectorException(f"Error deserializing record: {exc}") from exc

    async def delete(self, key: TKey, **kwargs: Any) -> None:
        """Delete a record.

        Args:
            key: The key.
            **kwargs: Additional arguments.

        """
        try:
            await self._inner_delete([key], **kwargs)
        except Exception as exc:
            raise MemoryConnectorException(f"Error deleting record: {exc}") from exc

    async def delete_batch(self, keys: Sequence[TKey], **kwargs: Any) -> None:
        """Delete a batch of records.

        Args:
            keys: The keys.
            **kwargs: Additional arguments.

        """
        try:
            await self._inner_delete(keys, **kwargs)
        except Exception as exc:
            raise MemoryConnectorException(f"Error deleting records: {exc}") from exc

    # region Internal Serialization methods

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
        """
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

    def deserialize(self, records: OneOrMany[Any | dict[str, Any]], **kwargs: Any) -> OneOrMany[TModel] | None:
        """Deserialize the store model to the data model.

        This method follows the following steps:
        1. Check if the data model has a deserialize method.
            Use that method to deserialize and return the result.
        2. Deserialize the store model to a dict, using the store specific method.
        3. Convert the dict to the data model, using the data model specific method.
        """
        if deserialized := self._deserialize_store_model_to_data_model(records, **kwargs):
            return deserialized

        if isinstance(records, Sequence):
            dict_records = self._deserialize_store_models_to_dicts(records, **kwargs)
            if self._container_mode:
                return self._deserialize_dict_to_data_model(dict_records, **kwargs)
            return [self._deserialize_dict_to_data_model(rec, **kwargs) for rec in dict_records]

        dict_record = self._deserialize_store_models_to_dicts([records], **kwargs)[0]
        if not dict_record:
            return None
        return self._deserialize_dict_to_data_model(dict_record, **kwargs)

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
            return self.data_model_definition.serialize(record, **kwargs)  # type: ignore
        if isinstance(record, VectorStoreModelFunctionSerdeProtocol):
            try:
                return record.serialize(**kwargs)
            except Exception as exc:
                raise VectorStoreModelSerializationException(f"Error serializing record: {exc}") from exc
        return None

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
        if isinstance(self.data_model_type, VectorStoreModelFunctionSerdeProtocol):
            try:
                if isinstance(record, Sequence):
                    return [self.data_model_type.deserialize(rec, **kwargs) for rec in record]
                return self.data_model_type.deserialize(record, **kwargs)
            except Exception as exc:
                raise VectorStoreModelSerializationException(f"Error deserializing record: {exc}") from exc
        return None

    def _serialize_data_model_to_dict(self, record: TModel, **kwargs: Any) -> OneOrMany[dict[str, Any]]:
        """This function is used if no serialize method is found on the data model.

        This will generally serialize the data model to a dict, should not be overridden by child classes.

        The output of this should be passed to the serialize_dict_to_store_model method.
        """
        if self.data_model_definition.to_dict:
            return self.data_model_definition.to_dict(record, **kwargs)
        if isinstance(record, VectorStoreModelPydanticProtocol):
            try:
                ret = record.model_dump()
                if not any(field.serialize_function is not None for field in self.data_model_definition.vector_fields):
                    return ret
                for field in self.data_model_definition.vector_fields:
                    if field.serialize_function:
                        assert field.name is not None  # nosec
                        ret[field.name] = field.serialize_function(ret[field.name])
                return ret
            except Exception as exc:
                raise VectorStoreModelSerializationException(f"Error serializing record: {exc}") from exc
        if isinstance(record, VectorStoreModelToDictFromDictProtocol):
            try:
                ret = record.to_dict()
                if not any(field.serialize_function is not None for field in self.data_model_definition.vector_fields):
                    return ret
                for field in self.data_model_definition.vector_fields:
                    if field.serialize_function:
                        assert field.name is not None  # nosec
                        ret[field.name] = field.serialize_function(ret[field.name])
                return ret
            except Exception as exc:
                raise VectorStoreModelSerializationException(f"Error serializing record: {exc}") from exc

        store_model = {}
        for field_name in self.data_model_definition.field_names:
            try:
                value = record[field_name] if isinstance(record, Mapping) else getattr(record, field_name)
                if func := getattr(self.data_model_definition.fields[field_name], "serialize_function", None):
                    value = func(value)
                store_model[field_name] = value
            except (AttributeError, KeyError) as exc:
                raise VectorStoreModelSerializationException(
                    f"Error serializing record, not able to get: {field_name}"
                ) from exc
        return store_model

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
        if isinstance(self.data_model_type, VectorStoreModelPydanticProtocol):
            try:
                if not any(field.serialize_function is not None for field in self.data_model_definition.vector_fields):
                    return self.data_model_type.model_validate(record)
                for field in self.data_model_definition.vector_fields:
                    if field.serialize_function:
                        record[field.name] = field.serialize_function(record[field.name])
                return self.data_model_type.model_validate(record)
            except Exception as exc:
                raise VectorStoreModelDeserializationException(f"Error deserializing record: {exc}") from exc
        if isinstance(self.data_model_type, VectorStoreModelToDictFromDictProtocol):
            try:
                if not any(field.serialize_function is not None for field in self.data_model_definition.vector_fields):
                    return self.data_model_type.from_dict(record)
                for field in self.data_model_definition.vector_fields:
                    if field.serialize_function:
                        record[field.name] = field.serialize_function(record[field.name])
                return self.data_model_type.from_dict(record)
            except Exception as exc:
                raise VectorStoreModelDeserializationException(f"Error deserializing record: {exc}") from exc
        data_model_dict: dict[str, Any] = {}
        for field_name in self.data_model_definition.fields:  # type: ignore
            try:
                value = record[field_name]
                if func := getattr(self.data_model_definition.fields[field_name], "deserialize_function", None):
                    value = func(value)
                data_model_dict[field_name] = value
            except KeyError as exc:
                raise VectorStoreModelDeserializationException(
                    f"Error deserializing record, not able to get: {field_name}"
                ) from exc
        if self.data_model_type is dict:
            return data_model_dict  # type: ignore
        return self.data_model_type(**data_model_dict)

    # region Internal Functions

    async def __aenter__(self):
        """Enter the context manager."""
        return self

    async def __aexit__(self, *args):
        """Exit the context manager."""
        await self.close()

    def __del__(self):
        """Delete the instance."""
        with contextlib.suppress(Exception):
            asyncio.get_running_loop().create_task(self.close())
