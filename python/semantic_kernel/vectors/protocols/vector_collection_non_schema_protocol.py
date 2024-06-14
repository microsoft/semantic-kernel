# Copyright (c) Microsoft. All rights reserved.


from typing import Protocol, runtime_checkable


@runtime_checkable
class VectorCollectionNonSchemaProtocol(Protocol):
    async def get_collection_names(self, **kwargs) -> list[str]:
        """Get the collection names."""
        ...

    async def collection_exists(self, collection_name: str, **kwargs) -> bool:
        """Check if the collection exists."""
        ...

    async def delete_collection(self, collection_name: str, **kwargs):
        """Delete a collection."""
        ...
