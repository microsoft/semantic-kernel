# Copyright (c) Microsoft. All rights reserved.


from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from semantic_kernel.data.protocols.data_model_serde_protocols import (
    DataModelFunctionSerdeProtocol,
    DataModelPydanticSerde,
    DataModelToDictFromDictProtocol,
)
from semantic_kernel.exceptions.memory_connector_exceptions import (
    DataModelDeserializationException,
    DataModelSerializationException,
    MemoryConnectorException,
)
from semantic_kernel.utils.experimental_decorator import experimental_class

TModel = TypeVar("TModel", bound=object)
TKey = TypeVar("TKey")


@experimental_class
class VectorRecordStoreBase(ABC, Generic[TModel, TKey]):
    def __init__(
        self,
        item_type: type[TModel],
        collection_name: str | None = None,
    ):
        """Create a VectorStoreBase instance.

        Args:
            item_type (type[TModel]): The data model type.
            key_type (type[TKey], optional): The key type. Defaults to None.
            collection_name (str, optional): The collection name. Defaults to None.

        Raises:
            ValueError: If the item type is not a data model.
            ValueError: If the item type does not have fields defined.
            ValueError: If the item type does not have the key field defined.
        """
        self.collection_name = collection_name
        if not hasattr(item_type, "__kernel_data_model__"):
            raise ValueError(f"Item type {item_type} must be a data model, use the @datamodel decorator")
        self._item_type: type[TModel] = item_type
        model_fields = getattr(item_type, "__kernel_data_model_fields__")
        if not model_fields:
            raise ValueError(f"Item type {item_type} must have fields defined")
        self._key_field = model_fields.key_field.name
        if not self._key_field:
            raise ValueError(f"Item type {item_type} must have the key field defined.")

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
        self, record: TModel, collection_name: str | None = None, generate_vectors: bool = True, **kwargs: Any
    ) -> TKey:
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
        self, records: list[TModel], collection_name: str | None = None, generate_vectors: bool = True, **kwargs: Any
    ) -> list[TKey]:
        """Upsert a batch of records.

        Args:
            records (list[TModel]): The record.
            collection_name (str, optional): The collection name. Defaults to None.
            generate_vectors (bool): Whether to generate vectors. Defaults to True.
                If there are no vector fields in the model or the vectors are created
                by the service, this is ignored, defaults to True.
            **kwargs (Any): Additional arguments.

        Returns:
            list[TKey]: The keys of the upserted records.
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

    def _validate_data_model(self, item_type: type[TModel]):
        """Internal function that should be overloaded by child classes to validate datatypes, etc.

        This should take the VectorStoreRecordDefinition from the item_type and validate it against the store.

        Checks should include, allowed naming of parameters, allowed data types, allowed vector dimensions.
        """
        return

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
        if isinstance(record, DataModelFunctionSerdeProtocol):
            try:
                return record.serialize()
            except Exception as exc:
                raise DataModelSerializationException(f"Error serializing record: {exc}") from exc
        if isinstance(record, DataModelPydanticSerde):
            try:
                return record.model_dump()
            except Exception as exc:
                raise DataModelSerializationException(f"Error serializing record: {exc}") from exc
        if isinstance(record, DataModelToDictFromDictProtocol):
            try:
                return record.to_dict()
            except Exception as exc:
                raise DataModelSerializationException(f"Error serializing record: {exc}") from exc

        store_model = {}
        for field in getattr(self._item_type, "__kernel_data_model_fields__"):
            try:
                store_model[field.name] = getattr(record, field.name)
            except AttributeError:
                raise DataModelSerializationException(f"Error serializing record: {field.name}")
        return store_model

    def _deserialize_store_model_to_data_model(self, record: Any | dict[str, Any]) -> TModel:
        """Internal function that should be overloaded by child classes to deserialize the store model to the data model.

        Similar to the serialize counterpart this process is done in two steps, first here a
        specific data type or structure from a service is translated to dict, then in the deserialize method of the datamodel (supplied by the user) the dict is translated to the data model itself.

        """  # noqa: E501
        if isinstance(self._item_type, DataModelFunctionSerdeProtocol):
            try:
                return self._item_type.deserialize(record)
            except Exception as exc:
                raise DataModelDeserializationException(f"Error deserializing record: {exc}") from exc
        if isinstance(self._item_type, DataModelPydanticSerde):
            try:
                return self._item_type.model_validate(record)
            except Exception as exc:
                raise DataModelDeserializationException(f"Error deserializing record: {exc}") from exc
        if isinstance(self._item_type, DataModelToDictFromDictProtocol):
            try:
                return self._item_type.from_dict(record)
            except Exception as exc:
                raise DataModelDeserializationException(f"Error deserializing record: {exc}") from exc

        if isinstance(record, dict):
            data_model = self._item_type()
            for field in getattr(self._item_type, "__kernel_data_model_fields__"):
                setattr(data_model, field.name, record.get(field.name))
            return data_model
        raise DataModelDeserializationException(
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

    # endregion
