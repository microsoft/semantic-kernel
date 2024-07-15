# Copyright (c) Microsoft. All rights reserved.

import asyncio
import contextlib
import logging
import types
from abc import abstractmethod
from collections.abc import Callable, Sequence
from inspect import signature
from typing import Any, Generic, TypeVar

from pydantic import model_validator

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.data.vector_store_model_definition import (
    VectorStoreRecordDefinition,
)
from semantic_kernel.data.vector_store_model_protocols import (
    VectorStoreModelFunctionSerdeProtocol,
    VectorStoreModelPydanticProtocol,
    VectorStoreModelToDictFromDictProtocol,
)
from semantic_kernel.data.vector_store_record_fields import (
    VectorStoreRecordDataField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.exceptions.memory_connector_exceptions import (
    MemoryConnectorException,
    VectorStoreModelDeserializationException,
    VectorStoreModelSerializationException,
    VectorStoreModelValidationError,
)
from semantic_kernel.kernel import Kernel
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.kernel_types import OneOrMany
from semantic_kernel.utils.experimental_decorator import experimental_class

TModel = TypeVar("TModel", bound=object)
TKey = TypeVar("TKey")

logger = logging.getLogger(__name__)


@experimental_class
class VectorStoreRecordCollection(KernelBaseModel, Generic[TKey, TModel]):
    collection_name: str
    data_model_type: type[TModel]
    data_model_definition: VectorStoreRecordDefinition
    kernel: Kernel | None = None
    _container_mode: bool = False
    _key_field: str = ""

    @model_validator(mode="before")
    @classmethod
    def validate_data_model_definition(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Validate the data model definition, if it isn't passed, try to get it from the data model type."""
        if not data.get("data_model_definition"):
            data["data_model_definition"] = getattr(data["data_model_type"], "__kernel_data_model_fields__", None)
        return data

    def model_post_init(self, __context: object | None = None):
        """Post init function that sets the key field and container mode values, and validates the datamodel."""
        if self.data_model_definition.key_field.name is None:
            raise ValueError("Key field must be defined and have a name in the data model definition.")
        self._key_field = self.data_model_definition.key_field.name
        self._container_mode = self.data_model_definition.container_mode

        if hasattr(self.data_model_type, "__kernel_data_model__"):
            self._validate_data_model()
        else:
            logger.debug(
                f"No data model validation performed on {self.data_model_type}, "
                "as it is not a DataModel, your input may be incorrect."
            )

    # region Overload Methods
    async def close(self):
        """Close the connection."""
        return

    @abstractmethod
    async def _inner_upsert(
        self,
        records: Sequence[Any],
        **kwargs: Any,
    ) -> Sequence[TKey]:
        """Upsert the records, this should be overridden by the child class.

        Args:
            records (Sequence[Any]): The records, the format is specific to the store.
            **kwargs (Any): Additional arguments, to be passed to the store.

        Returns:
            The keys of the upserted records.
        """
        ...

    @abstractmethod
    async def _inner_get(self, keys: Sequence[TKey], **kwargs: Any) -> OneOrMany[Any] | None:
        """Get the records, this should be overridden by the child class.

        Args:
            keys (Sequence[TKey]): The keys to get.
            **kwargs (Any): Additional arguments.

        Returns:
            The records from the store, not deserialized.
        """
        ...

    @abstractmethod
    async def _inner_delete(self, keys: Sequence[TKey], **kwargs: Any) -> None:
        """Delete the records, this should be overridden by the child class.

        Args:
            keys (Sequence[TKey]): The keys.
            **kwargs (Any): Additional arguments.
        """
        ...

    @property
    def supported_key_types(self) -> Sequence[type] | None:
        """Supply the types that keys are allowed to have. None means any."""
        return None

    @property
    def supported_vector_types(self) -> Sequence[type] | None:
        """Supply the types that vectors are allowed to have. None means any."""
        return None

    def _validate_data_model(self):
        """Internal function that should be overloaded by child classes to validate datatypes, etc.

        This should take the VectorStoreRecordDefinition from the item_type and validate it against the store.

        Checks should include, allowed naming of parameters, allowed data types, allowed vector dimensions.
        """
        model_sig = signature(self.data_model_type)
        key_type = model_sig.parameters[self._key_field].annotation.__args__[0]  # type: ignore
        if self.supported_key_types and key_type not in self.supported_key_types:
            raise VectorStoreModelValidationError(f"Key field must be one of {self.supported_key_types}")
        if not self.supported_vector_types:
            return
        for field_name, field in self.data_model_definition.fields.items():
            if isinstance(field, VectorStoreRecordVectorField):
                field_type = model_sig.parameters[field_name].annotation.__args__[0]
                if field_type.__class__ is types.UnionType:
                    field_type = field_type.__args__[0]
                if field_type not in self.supported_vector_types:
                    raise VectorStoreModelValidationError(
                        f"Vector field {field_name} must be one of {self.supported_vector_types}"
                    )
        return

    @abstractmethod
    def _serialize_dicts_to_store_models(self, records: Sequence[dict[str, Any]], **kwargs: Any) -> Sequence[Any]:
        """Serialize a list of dicts of the data to the store model.

        This method should be overridden by the child class to convert the dict to the store model.
        """
        ...

    @abstractmethod
    def _deserialize_store_models_to_dicts(self, records: Sequence[Any], **kwargs: Any) -> Sequence[dict[str, Any]]:
        """Deserialize the store models to a list of dicts.

        This method should be overridden by the child class to convert the store model to a list of dicts.
        """
        ...

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
        ...

    @abstractmethod
    async def does_collection_exist(self, **kwargs: Any) -> bool:
        """Check if the collection exists."""
        ...

    @abstractmethod
    async def delete_collection(self, **kwargs: Any) -> None:
        """Delete the collection."""
        ...

    # region Public Methods

    async def upsert(
        self,
        record: TModel,
        generate_embeddings: bool = False,
        **kwargs: Any,
    ) -> OneOrMany[TKey] | None:
        """Upsert a record.

        Args:
            record (TModel): The record.
            generate_embeddings (bool): Whether to generate vectors. Defaults to True.
                If there are no vector fields in the model or the vectors are created
                by the service, this is ignored, defaults to False.
            **kwargs (Any): Additional arguments.

        Returns:
            The key of the upserted record or a list of keys, when a container type is used.
        """
        if generate_embeddings:
            await self._add_vector_to_records(record)
        data = self.serialize(record)
        if not isinstance(data, Sequence):
            data = [data]
        try:
            results = await self._inner_upsert(data, **kwargs)
        except Exception as exc:
            raise MemoryConnectorException(f"Error upserting record: {exc}") from exc
        if self._container_mode:
            return results
        return results[0]

    async def upsert_batch(
        self,
        records: OneOrMany[TModel],
        generate_embeddings: bool = False,
        **kwargs: Any,
    ) -> Sequence[TKey]:
        """Upsert a batch of records.

        Args:
            records (Sequence[TModel] | TModel): The records to upsert, can be a list of records, or a single container.
            generate_embeddings (bool): Whether to generate vectors. Defaults to True.
                If there are no vector fields in the model or the vectors are created
                by the service, this is ignored, defaults to False.
            **kwargs (Any): Additional arguments.

        Returns:
            Sequence[TKey]: The keys of the upserted records, this is always a list,
            corresponds to the input or the items in the container.
        """
        if generate_embeddings:
            await self._add_vector_to_records(records)
        data = self.serialize(records)
        try:
            return await self._inner_upsert(data, **kwargs)  # type: ignore
        except Exception as exc:
            raise MemoryConnectorException(f"Error upserting records: {exc}") from exc

    async def get(self, key: TKey, **kwargs: Any) -> TModel | None:
        """Get a record.

        Args:
            key (TKey): The key.
            **kwargs (Any): Additional arguments.

        Returns:
            TModel: The record.
        """
        try:
            records = await self._inner_get([key])
        except Exception as exc:
            raise MemoryConnectorException(f"Error getting record: {exc}") from exc
        if not records:
            return None
        try:
            model_records = self.deserialize(records, keys=[key], **kwargs)
            if isinstance(model_records, Sequence):
                return model_records[0]
            return model_records
        except Exception as exc:
            raise MemoryConnectorException(f"Error deserializing record: {exc}") from exc

    async def get_batch(self, keys: Sequence[TKey], **kwargs: Any) -> OneOrMany[TModel] | None:
        """Get a batch of records.

        Args:
            keys (Sequence[TKey]): The keys.
            **kwargs (Any): Additional arguments.

        Returns:
            The records, either a list of TModel or the container type.
        """
        try:
            records = await self._inner_get(keys)
        except Exception as exc:
            raise MemoryConnectorException(f"Error getting record: {exc}") from exc
        if not records:
            return None
        try:
            return self.deserialize(records, keys=keys, **kwargs)
        except Exception as exc:
            raise MemoryConnectorException(f"Error deserializing record: {exc}") from exc

    async def delete(self, key: TKey, **kwargs: Any) -> None:
        """Delete a record.

        Args:
            key (TKey): The key.
            **kwargs (Any): Additional arguments.

        """
        try:
            await self._inner_delete([key], **kwargs)
        except Exception as exc:
            raise MemoryConnectorException(f"Error deleting record: {exc}") from exc

    async def delete_batch(self, keys: Sequence[TKey], **kwargs: Any) -> None:
        """Delete a batch of records.

        Args:
            keys (Sequence[TKey]): The keys.
            **kwargs (Any): Additional arguments.

        """
        try:
            await self._inner_delete(keys, **kwargs)
        except Exception as exc:
            raise MemoryConnectorException(f"Error deleting records: {exc}") from exc

    # region Internal Serialization methods

    def serialize(self, records: OneOrMany[TModel], **kwargs: Any) -> OneOrMany[Any] | None:
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
            return [self._deserialize_dict_to_data_model(rec, **kwargs) for rec in dict_records]
        dict_records = self._deserialize_store_models_to_dicts([records], **kwargs)
        if self._container_mode:
            return self._deserialize_dict_to_data_model(dict_records, **kwargs)
        # this case is single record in, single record out
        return self._deserialize_dict_to_data_model(dict_records[0])

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
        if self._container_mode and self.data_model_definition.serialize:
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
        if self._container_mode and self.data_model_definition.deserialize:
            return self.data_model_definition.deserialize(record, **kwargs)
        if isinstance(self.data_model_type, VectorStoreModelFunctionSerdeProtocol):
            try:
                if isinstance(record, Sequence):
                    return [self.data_model_type.deserialize(rec, **kwargs) for rec in record]
                return self.data_model_type.deserialize(record, **kwargs)
            except Exception as exc:
                raise VectorStoreModelSerializationException(f"Error serializing record: {exc}") from exc
        return None

    def _serialize_data_model_to_dict(self, record: TModel, **kwargs: Any) -> OneOrMany[dict[str, Any]]:
        """This function is used if no serialize method is found on the data model.

        This will generally serialize the data model to a dict, should not be overridden by child classes.

        The output of this should be passed to the serialize_dict_to_store_model method.
        """
        if isinstance(record, dict):
            return record
        if self._container_mode and self.data_model_definition.to_dict:
            return self.data_model_definition.to_dict(record, **kwargs)
        if isinstance(record, VectorStoreModelPydanticProtocol):
            try:
                return record.model_dump()
            except Exception as exc:
                raise VectorStoreModelSerializationException(f"Error serializing record: {exc}") from exc
        if isinstance(record, VectorStoreModelToDictFromDictProtocol):
            try:
                return record.to_dict()
            except Exception as exc:
                raise VectorStoreModelSerializationException(f"Error serializing record: {exc}") from exc

        store_model = {}
        for field_name in self.data_model_definition.field_names:  # type: ignore
            if (getter := getattr(record, "get", None)) and callable(getter):
                try:
                    value = record.get(field_name)  # type: ignore
                    if value:
                        store_model[field_name] = value
                except AttributeError:
                    raise VectorStoreModelSerializationException(f"Error serializing record: {field_name}")
            else:
                try:
                    store_model[field_name] = getattr(record, field_name)
                except AttributeError:
                    raise VectorStoreModelSerializationException(f"Error serializing record: {field_name}")
        return store_model

    def _deserialize_dict_to_data_model(self, record: OneOrMany[dict[str, Any]], **kwargs: Any) -> TModel:
        """This function is used if no deserialize method is found on the data model.

        This method is the second step and will deserialize a dict to the data model,
        should not be overridden by child classes.

        The input of this should come from the _deserialized_store_model_to_dict function.
        """
        if self._container_mode and self.data_model_definition.from_dict:
            if not isinstance(record, Sequence):
                record = [record]
            return self.data_model_definition.from_dict(record, **kwargs)
        if isinstance(record, Sequence):
            if len(record) > 1:
                raise ValueError(
                    "Cannot deserialize multiple records to a single record unless you are using a container."
                )
            record = record[0]
        if self.data_model_type is dict:
            return record  # type: ignore
        if isinstance(self.data_model_type, VectorStoreModelPydanticProtocol):
            try:
                return self.data_model_type.model_validate(record)
            except Exception as exc:
                raise VectorStoreModelDeserializationException(f"Error deserializing record: {exc}") from exc
        if isinstance(self.data_model_type, VectorStoreModelToDictFromDictProtocol):
            try:
                return self.data_model_type.from_dict(record)
            except Exception as exc:
                raise VectorStoreModelDeserializationException(f"Error deserializing record: {exc}") from exc
        data_model_dict: dict[str, Any] = {}
        for field_name in self.data_model_definition.fields:  # type: ignore
            data_model_dict[field_name] = record.get(field_name)
        if isinstance(self.data_model_type, dict):
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

    async def _add_vector_to_records(self, records: OneOrMany[TModel], **kwargs) -> OneOrMany[TModel]:
        """Vectorize the vector record."""
        # dict of embedding_field.name and tuple of record, settings, field_name
        embeddings_to_make: list[tuple[str, str, dict[str, PromptExecutionSettings], Callable | None]] = []

        for name, field in self.data_model_definition.fields.items():  # type: ignore
            if (
                not isinstance(field, VectorStoreRecordDataField)
                or not field.has_embedding
                or not field.embedding_property_name
            ):
                continue
            embedding_field_name = field.embedding_property_name
            embedding_field = self.data_model_definition.fields.get(embedding_field_name)
            assert isinstance(embedding_field, VectorStoreRecordVectorField)  # nosec
            if not embedding_field.local_embedding:
                continue
            settings = embedding_field.embedding_settings
            cast_callable = embedding_field.cast_function
            embeddings_to_make.append((name, embedding_field_name, settings, cast_callable))

        for field_to_embed, field_to_store, settings, cast_callable in embeddings_to_make:
            if not self.kernel:
                raise MemoryConnectorException("Kernel is required to create embeddings.")
            await self.kernel.add_embedding_to_object(
                inputs=records,
                field_to_embed=field_to_embed,
                field_to_store=field_to_store,
                execution_settings=settings,
                container_mode=self._container_mode,
                cast_function=cast_callable,
                **kwargs,
            )
        return records
