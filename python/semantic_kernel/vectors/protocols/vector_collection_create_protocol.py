# Copyright (c) Microsoft. All rights reserved.

from typing import Protocol, runtime_checkable


@runtime_checkable
class VectorCollectionCreateProtocol(Protocol):
    async def create_collection(self, collection_name: str, **kwargs):
        """Create a new collection."""
        ...
