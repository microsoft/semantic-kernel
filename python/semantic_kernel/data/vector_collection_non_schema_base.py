# Copyright (c) Microsoft. All rights reserved.


from abc import ABC, abstractmethod

from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class VectorCollectionNonSchemaBase(ABC):
    @abstractmethod
    async def get_collection_names(self, **kwargs) -> list[str]:
        """Get the collection names."""
        ...

    @abstractmethod
    async def collection_exists(self, collection_name: str, **kwargs) -> bool:
        """Check if the collection exists."""
        ...

    @abstractmethod
    async def delete_collection(self, collection_name: str, **kwargs):
        """Delete a collection."""
        ...
