# Copyright (c) Microsoft. All rights reserved.


from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from semantic_kernel.exceptions.memory_connector_exceptions import MemoryConnectorException

DataModelT = TypeVar("DataModelT", bound=object)
KeyTypeT = TypeVar("KeyTypeT")


class MemoryRecordServiceBase(ABC, Generic[DataModelT, KeyTypeT]):
    def __init__(
        self, item_type: type[DataModelT], key_type: KeyTypeT | None = None, collection_name: str | None = None
    ):
        """Initialize the memory record service.

        Args:
            item_type (DataModelT): The item type.
            key_type (KeyTypeT, optional): The key type. Defaults to None.
            collection_name (str, optional): The collection name. Defaults to None.
                This can be set here, or in other methods that take a collection_name parameter.
                One of those must not be None.

        Raises:
            ValueError: If the item type is not a data model.
        """
        if not hasattr(item_type, "__sk_data_model__"):
            raise ValueError(f"Item type {item_type} must be a data model, use the @datamodel decorator")
        self._item_type: type[DataModelT] = item_type
        if not key_type:
            self._key_type: KeyTypeT = item_type.__sk_data_model_fields__.key_field
        else:
            self._key_type: KeyTypeT = key_type
        self.collection_name = collection_name

    @abstractmethod
    async def upsert(self, record: DataModelT, collection_name: str | None = None, **kwargs) -> KeyTypeT:
        """Upsert a record.

        Args:
            record (DataModelT): The record.
            collection_name (str, optional): The collection name. Defaults to None.
                This can be set here, or in other methods that take a collection_name parameter.
                One of those must not be None.
            kwargs: Additional keyword arguments.
        """
        pass

    @abstractmethod
    async def upsert_batch(
        self, records: list[DataModelT], collection_name: str | None = None, **kwargs
    ) -> list[KeyTypeT]:
        """Upsert a batch of records.

        Args:
            records (list[DataModelT]): The record.
            collection_name (str, optional): The collection name. Defaults to None.
                This can be set here, or in other methods that take a collection_name parameter.
                One of those must not be None.
            kwargs: Additional keyword arguments.
        """
        pass

    @abstractmethod
    async def get(self, key: KeyTypeT, collection_name: str | None = None, **kwargs) -> DataModelT:
        """Get a record.

        Args:
            key (KeyTypeT): The key of the requested record.
            collection_name (str, optional): The collection name. Defaults to None.
                This can be set here, or in other methods that take a collection_name parameter.
                One of those must not be None.
            kwargs: Additional keyword arguments.
        """
        pass

    @abstractmethod
    async def get_batch(self, keys: list[KeyTypeT], collection_name: str | None = None, **kwargs) -> list[DataModelT]:
        """Get a batch of records.

        Args:
            keys (list[KeyTypeT]): The key of the requested record.
            collection_name (str, optional): The collection name. Defaults to None.
                This can be set here, or in other methods that take a collection_name parameter.
                One of those must not be None.
            kwargs: Additional keyword arguments.
        """
        pass

    @abstractmethod
    async def delete(self, key: KeyTypeT, collection_name: str | None = None, **kwargs):
        """Delete a record.

        Args:
            key (KeyTypeT): The key of the record to be deleted.
            collection_name (str, optional): The collection name. Defaults to None.
                This can be set here, or in other methods that take a collection_name parameter.
                One of those must not be None.
            kwargs: Additional keyword arguments.
        """
        pass

    @abstractmethod
    async def delete_batch(self, keys: list[KeyTypeT], collection_name: str | None = None, **kwargs):
        """Delete a batch of records.

        Args:
            keys (list[KeyTypeT]): The keys of the records to be deleted.
            collection_name (str, optional): The collection name. Defaults to None.
                This can be set here, or in other methods that take a collection_name parameter.
                One of those must not be None.
            kwargs: Additional keyword arguments.
        """
        pass

    # region Internal Functions

    def _get_collection_name(self, collection_name: str | None = None):
        """Gets the collection name, ensuring it is lower case.

        First tries the supplied argument, then self.
        """
        collection_name = collection_name or self.collection_name or None
        if not collection_name:
            raise MemoryConnectorException("Error: collection_name not set.")
        return collection_name
    
    def _validate_data_model(self, item_type: type[DataModelT]):
        """Internal function that should be overloaded by child classes to validate datatypes, etc."""
        return

    # endregion
