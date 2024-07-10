# Copyright (c) Microsoft. All rights reserved.


from abc import ABC, abstractmethod

from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class VectorStoreBase(ABC):
    """Base class for vector collection store."""

    def __init__(self, default_collection_name: str | None = None, **kwargs):
        """Initialize the vector collection store."""
        self._collection_names: list[str] = []
        if default_collection_name:
            self._collection_names.append(default_collection_name)
        self._vector_record_stores = {}

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
