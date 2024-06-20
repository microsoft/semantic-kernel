# Copyright (c) Microsoft. All rights reserved.

import logging
from abc import ABC, abstractmethod
from inspect import signature
from typing import Any, Generic, TypeVar

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.data.models.vector_store_model_definition import (
    VectorStoreContainerDefinition,
    VectorStoreRecordDefinition,
)
from semantic_kernel.data.models.vector_store_record_fields import (
    VectorStoreRecordDataField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.data.protocols.vector_store_model_serde_protocols import (
    VectorStoreModelFunctionSerdeProtocol,
    VectorStoreModelPydanticProtocol,
    VectorStoreModelToDictFromDictProtocol,
)
from semantic_kernel.exceptions.memory_connector_exceptions import (
    MemoryConnectorException,
    VectorStoreModelDeserializationException,
    VectorStoreModelSerializationException,
)
from semantic_kernel.kernel import Kernel
from semantic_kernel.kernel_types import OneOrMany
from semantic_kernel.utils.experimental_decorator import experimental_class

TModel = TypeVar("TModel", bound=object)
TKey = TypeVar("TKey")

logger = logging.getLogger(__name__)


@experimental_class
class VectorRecordStoreBase(ABC, Generic[TKey, TModel]):
    def __init__(
        self,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        collection_name: str | None = None,
        kernel: Kernel | None = None,
    ):
        """Create a VectorStoreBase instance.

        Args:
            data_model_type (type[TModel]): The data model type.
            data_model_definition (VectorStoreRecordDefinition | VectorStoreContainerDefinition):
                The model fields when supplied, can be a VectorStoreRecordDefinition or VectorStoreContainerDefinition.
                The VectorStoreRecordDefinition is used when the data model are single instances of data records.
                When a container style data model is used, for instance a pandas DataFrame,
                the VectorStoreContainerDefinition must be used.
                This field supplied directly takes precedence over the fields defined in the item_type.
            collection_name (str, optional): The collection name. Defaults to None.
            kernel (Kernel, optional): The kernel, used if embeddings need to be created.

        Raises:
            ValueError: If the item type is not a data model.
            ValueError: If the item type does not have fields defined.
            ValueError: If the item type does not have the key field defined.
        """
        self.collection_name = collection_name
        self._kernel = kernel
        self._data_model_type: type[TModel] = data_model_type
        self._data_model_definition: VectorStoreRecordDefinition = data_model_definition or getattr(
            self._data_model_type, "__kernel_data_model_fields__"
        )
        if not self._data_model_definition:
            raise ValueError(
                f"Item type {data_model_type} must have the model fields defined or it needs to be passed in directly."
            )
        self._container_mode = isinstance(self._data_model_definition, VectorStoreContainerDefinition)
        self._key_field = self._data_model_definition.key_field.name
        if not self._key_field:
            raise ValueError(
                f"The key field must be defined, either in the datamodel ({self._data_model_type}) "
                f"or the model_fields ({self._data_model_definition})."
            )
        if hasattr(self._data_model_type, "__kernel_data_model__"):
            self._validate_data_model()
        else:
            logger.debug(
                f"No data model validation performed on {self._data_model_type}, "
                "as it is not a DataModel, your input may be incorrect."
            )

    async def __aenter__(self):
        """Enter the context manager."""
        return self

    async def __aexit__(self, *args):
        """Exit the context manager."""
        await self.close()

    async def close(self):
        """Close the connection."""
        pass

    # region Abstract methods

    @abstractmethod
    async def upsert(
        self,
        record: TModel,
        collection_name: str | None = None,
        generate_vectors: bool = True,
        **kwargs: Any,
    ) -> TKey | None:
        """Upsert a record.

        Args:
            record (TModel): The record.
            collection_name (str, optional): The collection name. Defaults to None.
            generate_vectors (bool): Whether to generate vectors. Defaults to True.
                If there are no vector fields in the model or the vectors are created
                by the service, this is ignored, defaults to True.
            **kwargs (Any): Additional arguments.

        Returns:
            TKey: The key of the upserted record.
        """

    @abstractmethod
    async def upsert_batch(
        self,
        records: OneOrMany[TModel],
        collection_name: str | None = None,
        generate_vectors: bool = True,
        **kwargs: Any,
    ) -> list[TKey]:
        """Upsert a batch of records.

        Args:
            records (list[TModel] | TModel): The records to upsert, can be a list of records, or a single container.
            collection_name (str, optional): The collection name. Defaults to None.
            generate_vectors (bool): Whether to generate vectors. Defaults to True.
                If there are no vector fields in the model or the vectors are created
                by the service, this is ignored, defaults to True.
            **kwargs (Any): Additional arguments.

        Returns:
            list[TKey]: The keys of the upserted records, this is always a list,
            corresponds to the input or the items in the container.
        """

    @abstractmethod
    async def get(self, key: TKey, collection_name: str | None = None, **kwargs: Any) -> TModel:
        """Get a record.

        Args:
            key (TKey): The key.
            collection_name (str, optional): The collection name. Defaults to None.
            **kwargs (Any): Additional arguments.

        Returns:
            TModel: The record.
        """

    @abstractmethod
    async def get_batch(self, keys: list[TKey], collection_name: str | None = None, **kwargs: Any) -> list[TModel]:
        """Get a batch of records.

        Args:
            keys (list[TKey]): The keys.
            collection_name (str, optional): The collection name. Defaults to None.
            **kwargs (Any): Additional arguments.

        Returns:
            list[TModel]: The records.
        """

    @abstractmethod
    async def delete(self, key: TKey, collection_name: str | None = None, **kwargs: Any) -> None:
        """Delete a record.

        Args:
            key (TKey): The key.
            collection_name (str, optional): The collection name. Defaults to None.
            **kwargs (Any): Additional arguments.

        """

    @abstractmethod
    async def delete_batch(self, keys: list[TKey], collection_name: str | None = None, **kwargs: Any) -> None:
        """Delete a batch of records.

        Args:
            keys (list[TKey]): The keys.
            collection_name (str, optional): The collection name. Defaults to None.
            **kwargs (Any): Additional arguments.

        """

    # endregion
    # region Overloadable Methods

    @property
    def supported_key_types(self) -> list[type] | None:
        """Supply the types that keys are allowed to have. None means any."""
        return None

    @property
    def supported_vector_types(self) -> list[type] | None:
        """Supply the types that vectors are allowed to have. None means any."""
        return None

    def _validate_data_model(self):
        """Internal function that should be overloaded by child classes to validate datatypes, etc.

        This should take the VectorStoreRecordDefinition from the item_type and validate it against the store.

        Checks should include, allowed naming of parameters, allowed data types, allowed vector dimensions.
        """
        model_sig = signature(self._data_model_type)
        key_type = model_sig.parameters[self._key_field].annotation.__args__[0]  # type: ignore
        if self.supported_key_types and key_type not in self.supported_key_types:
            raise ValueError(f"Key field must be one of {self.supported_key_types}")
        return

    def _convert_model_to_list_of_dicts(self, records: OneOrMany[TModel]) -> list[dict[str, Any]]:
        """Convert the data model a list of dicts.

        Can be used as is, or overwritten by a subclass to return proper types.
        """
        if self._container_mode:
            return self._data_model_definition.serialize(records)  # type: ignore
        if not isinstance(records, list):
            raise ValueError("Records must be a list, or container_mode must be used.")
        return [self._serialize_data_model_to_store_model(record) for record in records]

    def _convert_search_result_to_data_model(self, search_result: Any):
        """Convert the data model a list of dicts.

        Can be used as is, or overwritten by a subclass to return proper types.
        """
        if self._container_mode:
            return self._data_model_definition.deserialize(search_result)  # type: ignore
        return [self._deserialize_store_model_to_data_model(res) for res in search_result]

    def _serialize_data_model_to_store_model(self, record: TModel) -> dict[str, Any]:
        """Internal function that should be overloaded by child classes to serialize the data model to the store model.

        The actual translation to and from is done in two stages,
        here and in the serialize method of the datamodel (supplied by the user).
        Checks on names and data types are ideally done when creating the store model,
        by the validate_data_model function.

        The way the developer wants to represent their data should be done inside the serialize method.

        This function can only add casting the dict to a specific format for that datasource,
        it should not alter the dict itself.
        It might include translating a flat dict, into a nested structure for
        metadata vs vector vs data vs key, or something similar, but nothing more.
        """
        if isinstance(record, VectorStoreModelFunctionSerdeProtocol):
            try:
                return record.serialize()
            except Exception as exc:
                raise VectorStoreModelSerializationException(f"Error serializing record: {exc}") from exc
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
        for field_name in self._data_model_definition.field_names:  # type: ignore
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

    def _deserialize_store_model_to_data_model(self, record: Any | dict[str, Any]) -> TModel:
        """Internal function that should be overloaded by child classes to deserialize the store model to the data model.

        Similar to the serialize counterpart this process is done in two steps, first here a
        specific data type or structure from a service is translated to dict, then in the deserialize method of the datamodel (supplied by the user) the dict is translated to the data model itself.

        """  # noqa: E501
        if isinstance(self._data_model_type, VectorStoreModelFunctionSerdeProtocol):
            try:
                return self._data_model_type.deserialize(record)
            except Exception as exc:
                raise VectorStoreModelDeserializationException(f"Error deserializing record: {exc}") from exc
        if isinstance(self._data_model_type, VectorStoreModelPydanticProtocol):
            try:
                return self._data_model_type.model_validate(record)
            except Exception as exc:
                raise VectorStoreModelDeserializationException(f"Error deserializing record: {exc}") from exc
        if isinstance(self._data_model_type, VectorStoreModelToDictFromDictProtocol):
            try:
                return self._data_model_type.from_dict(record)
            except Exception as exc:
                raise VectorStoreModelDeserializationException(f"Error deserializing record: {exc}") from exc
        if isinstance(record, dict):
            data_model_dict: dict[str, Any] = {}
            for field_name in self._data_model_definition.fields:  # type: ignore
                data_model_dict[field_name] = record.get(field_name)
            if isinstance(self._data_model_type, dict):
                return data_model_dict  # type: ignore
            return self._data_model_type(**data_model_dict)
        raise VectorStoreModelDeserializationException(
            "No way found to deserialize the record, please add a serialize method or override this function."
        )

    # endregion
    # region Internal Functions

    def _get_collection_name(self, collection_name: str | None = None):
        """Gets the collection name, ensuring it is lower case.

        First tries the supplied argument, then self.
        """
        collection_name = collection_name or self.collection_name or None
        if not collection_name:
            raise MemoryConnectorException("Error: collection_name not set.")
        return collection_name

    async def _add_vector_to_records(self, records: OneOrMany[TModel], **kwargs) -> OneOrMany[TModel]:
        """Vectorize the vector record."""
        # dict of embedding_field.name and tuple of record, settings, field_name
        embeddings_to_make: list[tuple[str, str, dict[str, PromptExecutionSettings]]] = []

        for name, field in self._data_model_definition.fields.items():  # type: ignore
            if (
                not isinstance(field, VectorStoreRecordDataField)
                or not field.has_embedding
                or not field.embedding_property_name
            ):
                continue
            embedding_field_name = field.embedding_property_name
            embedding_field = self._data_model_definition.fields.get(embedding_field_name)
            assert isinstance(embedding_field, VectorStoreRecordVectorField)  # nosec
            if not embedding_field.local_embedding:
                continue
            settings = embedding_field.embedding_settings
            embeddings_to_make.append((name, embedding_field_name, settings))

        for field_to_embed, field_to_store, settings in embeddings_to_make:
            if not self._kernel:
                raise MemoryConnectorException("Kernel is required to create embeddings.")
            await self._kernel.add_embedding_to_object(records, field_to_embed, field_to_store, settings, **kwargs)
        return records

    # endregion
