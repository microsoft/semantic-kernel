# Copyright (c) Microsoft. All rights reserved.


from typing import Any, Protocol, runtime_checkable

from semantic_kernel.utils.experimental_decorator import experimental_class


@runtime_checkable
@experimental_class
class VectorCollectionReadProtocol(Protocol):
    async def list_collection_names(self, **kwargs) -> list[str]:
        """Get the names of all collections."""
        ...

    async def collection_exists(self, collection_name: str | None = None, **kwargs) -> bool:
        """Check if a collection exists."""
        ...

    async def delete_collection(self, collection_name: str | None = None, **kwargs) -> None:
        """Delete a collection."""
        ...


@runtime_checkable
@experimental_class
class VectorCollectionCreateProtocol(Protocol):
    async def create_collection(self, collection_name: str | None = None, **kwargs):
        """Create a new collection."""
        ...


@runtime_checkable
@experimental_class
class VectorCollectionProtocol(Protocol):
    async def list_collection_names(self, **kwargs) -> list[str]:
        """Get the names of all collections."""
        ...

    async def collection_exists(self, collection_name: str | None = None, **kwargs: Any) -> bool:
        """Check if a collection exists."""
        ...

    async def delete_collection(self, collection_name: str | None = None, **kwargs: Any) -> None:
        """Delete a collection."""
        ...

    async def create_collection(self, collection_name: str | None = None, **kwargs) -> Any:
        """Create a new collection."""
        ...
