# Copyright (c) Microsoft. All rights reserved.


from abc import ABC, abstractmethod

from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class VectorCollectionStoreBase(ABC):
    @abstractmethod
    async def list_collection_names(self, **kwargs) -> list[str]:
        """Get the names of all collections."""
        ...

    @abstractmethod
    async def collection_exists(self, collection_name: str, **kwargs) -> bool:
        """Check if a collection exists."""
        ...

    @abstractmethod
    async def delete_collection(self, collection_name: str, **kwargs) -> None:
        """Delete a collection."""
        ...
