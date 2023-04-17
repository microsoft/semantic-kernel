# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import Any, List, Optional

from semantic_kernel.memory.storage.data_entry import DataEntry


class DataStoreBase(ABC):
    @abstractmethod
    async def get_collections_async(self) -> List[str]:
        pass

    @abstractmethod
    async def get_all_async(self, collection: str) -> List[Any]:
        pass

    @abstractmethod
    async def get_async(self, collection: str, key: str) -> Optional[DataEntry]:
        pass

    @abstractmethod
    async def put_async(self, collection: str, value: Any) -> DataEntry:
        pass

    @abstractmethod
    async def remove_async(self, collection: str, key: str) -> None:
        pass

    @abstractmethod
    async def get_value_async(self, collection: str, key: str) -> Any:
        pass

    @abstractmethod
    async def put_value_async(self, collection: str, key: str, value: Any) -> None:
        pass
