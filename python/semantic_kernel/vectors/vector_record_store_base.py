# Copyright (c) Microsoft. All rights reserved.


from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from semantic_kernel.exceptions.memory_connector_exceptions import MemoryConnectorException
from semantic_kernel.vectors.protocols.data_model_serde_protocol import DataModelSerdeProtocol

TModel = TypeVar("TModel", bound=object)
TKey = TypeVar("TKey")


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

    # region Internal Functions

    def _get_collection_name(self, collection_name: str | None = None):
        """Gets the collection name, ensuring it is lower case.

        First tries the supplied argument, then self.
        """
        collection_name = collection_name or self.collection_name or None
        if not collection_name:
            raise MemoryConnectorException("Error: collection_name not set.")
        return collection_name

    def _validate_data_model(self, item_type: type[TModel]):
        """Internal function that should be overloaded by child classes to validate datatypes, etc."""
        return

    def _serialize_data_model_to_store_model(self, record: TModel) -> dict[str, Any]:
        """Internal function that should be overloaded by child classes to serialize the data model to the store model."""  # noqa: E501
        if isinstance(record, DataModelSerdeProtocol):
            return record.serialize()
        raise ValueError("Item type must implement the DataModelSerdeProtocol")

    def _deserialize_store_model_to_data_model(self, record: dict[str, Any]) -> TModel:
        """Internal function that should be overloaded by child classes to deserialize the store model to the data model."""  # noqa: E501
        if isinstance(self._item_type, DataModelSerdeProtocol):
            return self._item_type.deserialize(record)
        raise ValueError("Item type must implement the DataModelSerdeProtocol")

    # endregion
