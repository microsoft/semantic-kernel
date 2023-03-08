# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import List, Any


class MemoryStorageBase(ABC):
    @abstractmethod
    async def get_collection_async(self) -> List[str]:
        pass

    @abstractmethod
    async def get_all_async(self, collection: str) -> List[Any]:
        pass

    @abstractmethod
    async def get_async(self, collection: str, key: str) -> Any:
        pass

    @abstractmethod
    async def put_async(self, collection: str, value: Any) -> Any:
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

    