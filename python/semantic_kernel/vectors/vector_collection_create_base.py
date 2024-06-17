# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod

from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class VectorCollectionCreateBase(ABC):
    @abstractmethod
    async def create_collection(self, collection_name: str, **kwargs):
        """Create a new collection."""
        ...
