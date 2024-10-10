# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import Mapping, Sequence
from typing import Any, ClassVar, TypeVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from pydantic import Field

from semantic_kernel.data.vector_store_model_definition import (
    VectorStoreRecordDefinition,
)
from semantic_kernel.data.vector_store_record_collection import (
    VectorStoreRecordCollection,
)
from semantic_kernel.kernel_types import OneOrMany

KEY_TYPES = str | int | float

TModel = TypeVar("TModel")


class VolatileCollection(VectorStoreRecordCollection[KEY_TYPES, TModel]):
    """Volatile Collection."""

    inner_storage: dict[KEY_TYPES, dict] = Field(default_factory=dict)
    supported_key_types: ClassVar[list[str] | None] = ["str", "int", "float"]

    def __init__(
        self,
        collection_name: str,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition | None = None,
    ):
        """Create a Volatile Collection."""
        super().__init__(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=collection_name,
        )

    @override
    async def _inner_delete(self, keys: Sequence[KEY_TYPES], **kwargs: Any) -> None:
        for key in keys:
            self.inner_storage.pop(key, None)

    @override
    async def _inner_get(
        self, keys: Sequence[KEY_TYPES], **kwargs: Any
    ) -> Any | OneOrMany[TModel] | None:
        return [self.inner_storage[key] for key in keys if key in self.inner_storage]

    @override
    async def _inner_upsert(
        self, records: Sequence[Any], **kwargs: Any
    ) -> Sequence[KEY_TYPES]:
        updated_keys = []
        for record in records:
            key = (
                record[self._key_field_name]
                if isinstance(record, Mapping)
                else getattr(record, self._key_field_name)
            )
            self.inner_storage[key] = record
            updated_keys.append(key)
        return updated_keys

    def _deserialize_store_models_to_dicts(
        self, records: Sequence[Any], **kwargs: Any
    ) -> Sequence[dict[str, Any]]:
        return records

    def _serialize_dicts_to_store_models(
        self, records: Sequence[dict[str, Any]], **kwargs: Any
    ) -> Sequence[Any]:
        return records

    @override
    async def create_collection(self, **kwargs: Any) -> None:
        pass

    @override
    async def delete_collection(self, **kwargs: Any) -> None:
        self.inner_storage = {}

    @override
    async def does_collection_exist(self, **kwargs: Any) -> bool:
        return True
