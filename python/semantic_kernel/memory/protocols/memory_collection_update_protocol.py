# Copyright (c) Microsoft. All rights reserved.


from typing import Protocol, runtime_checkable


@runtime_checkable()
class MemoryCollectionUpdateProtocol(Protocol):
    async def get_collection_names(self, **kwargs) -> list[str]:
        """Get all collection names."""
        ...

    async def collection_exists(self, collection_name: str | None = None, **kwargs) -> bool:
        """Check if a collection exists."""
        ...

    async def delete_collection(self, collection_name: str | None = None, **kwargs):
        """Delete a collection."""
        ...
