# Copyright (c) Microsoft. All rights reserved.


from abc import ABC, abstractmethod
from typing import Generic, TypeVar

DataModelT = TypeVar("DataModelT", bound=object)
KeyTypeT = TypeVar("KeyTypeT")


class MemoryRecordServiceBase(ABC, Generic[DataModelT, KeyTypeT]):
    def __init__(self, item_type: DataModelT, key_type: KeyTypeT | None = None):
        if not hasattr(item_type, "__sk_data_model__"):
            raise ValueError(f"Item type {item_type} must be a data model, use the @datamodel decorator")
        self._item_type: DataModelT = item_type
        if not key_type:
            self._key_type: KeyTypeT = item_type.__sk_data_model_fields__.key_field
        else:
            self._key_type: KeyTypeT = key_type

    @abstractmethod
    async def upsert(self, collection_name: str, record: DataModelT, **kwargs) -> KeyTypeT:
        pass

    @abstractmethod
    async def upsert_batch(self, collection_name: str, records: list[DataModelT], **kwargs) -> list[KeyTypeT]:
        pass

    @abstractmethod
    async def get(self, collection_name: str, key: KeyTypeT, **kwargs) -> DataModelT:
        pass

    @abstractmethod
    async def get_batch(self, collection_name: str, keys: list[KeyTypeT], **kwargs) -> list[DataModelT]:
        pass

    @abstractmethod
    async def delete(self, collection_name: str, key: KeyTypeT, **kwargs):
        pass

    @abstractmethod
    async def delete_batch(self, collection_name: str, keys: list[KeyTypeT], **kwargs):
        pass
