# Copyright (c) Microsoft. All rights reserved.


from abc import abstractmethod
from collections.abc import Sequence
from typing import Any

from pydantic import Field

from semantic_kernel.data.record_definition.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_storage.vector_store_record_collection import VectorStoreRecordCollection
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class VectorStore(KernelBaseModel):
    """Base class for vector stores."""

    vector_record_collections: dict[str, VectorStoreRecordCollection] = Field(default_factory=dict)
    managed_client: bool = True

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

    async def __aenter__(self) -> "VectorStore":
        """Enter the context manager."""
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager.

        Should be overridden by subclasses, if necessary.

        If the client is passed in the constructor, it should not be closed,
        in that case the managed_client should be set to False.
        """
        pass  # pragma: no cover
