# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import Sequence
from typing import Any, TypeVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


from semantic_kernel.connectors.memory.volatile.volatile_collection import VolatileCollection
from semantic_kernel.data.vector_store import VectorStore
from semantic_kernel.data.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_store_record_collection import VectorStoreRecordCollection
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)

TModel = TypeVar("TModel")


@experimental_class
class VolatileStore(VectorStore):
    """Create a Volatile Vector Store."""

    @override
    async def list_collection_names(self, **kwargs) -> Sequence[str]:
        return list(self.vector_record_collections.keys())

    @override
    def get_collection(
        self,
        collection_name: str,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        **kwargs: Any,
    ) -> "VectorStoreRecordCollection":
        if collection_name not in self.vector_record_collections:
            self.vector_record_collections[collection_name] = VolatileCollection(
                data_model_type=data_model_type,
                data_model_definition=data_model_definition,
                collection_name=collection_name,
            )
        return self.vector_record_collections[collection_name]
