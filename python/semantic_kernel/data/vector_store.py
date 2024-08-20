# Copyright (c) Microsoft. All rights reserved.


from abc import abstractmethod
from collections.abc import Sequence
from typing import Any

from pydantic import Field

from semantic_kernel.data.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_store_record_collection import VectorStoreRecordCollection
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class VectorStore(KernelBaseModel):
    """Base class for vector stores."""

    vector_record_collections: dict[str, VectorStoreRecordCollection] = Field(default_factory=dict)

    @abstractmethod
    def get_collection(
        self,
        collection_name: str,
        data_model_type: type[object],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        **kwargs: Any,
    ) -> VectorStoreRecordCollection:
        """Get a vector record store."""
        ...  # pragma: no cover

    @abstractmethod
    async def list_collection_names(self, **kwargs) -> Sequence[str]:
        """Get the names of all collections."""
        ...  # pragma: no cover
