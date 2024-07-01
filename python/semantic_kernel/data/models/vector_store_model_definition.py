# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Protocol

from semantic_kernel.data.models.vector_store_record_fields import (
    VectorStoreRecordDataField,
    VectorStoreRecordField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.exceptions.memory_connector_exceptions import VectorStoreModelException


class ToDictProtocol(Protocol):
    def __call__(self, record: Any, **kwargs: Any) -> list[dict[str, Any]]: ...  # noqa: D102


class FromDictProtocol(Protocol):
    def __call__(self, records: list[dict[str, Any]], **kwargs: Any) -> Any: ...  # noqa: D102


class SerializeProtocol(Protocol):
    def __call__(self, record: Any, **kwargs: Any) -> Any: ...  # noqa: D102


class DeserializeProtocol(Protocol):
    def __call__(self, records: Any, **kwargs: Any) -> Any: ...  # noqa: D102


@dataclass
class VectorStoreRecordDefinition:
    """Memory record definition."""

    key_field_name: str = field(init=False)
    fields: dict[str, VectorStoreRecordField]
    container_mode: bool = False
    to_dict: ToDictProtocol | None = None
    from_dict: FromDictProtocol | None = None
    serialize: SerializeProtocol | None = None
    deserialize: DeserializeProtocol | None = None

    @cached_property
    def field_names(self) -> list[str]:
        """Get the names of the fields."""
        return list(self.fields.keys())

    @property
    def key_field(self) -> "VectorStoreRecordKeyField":
        """Get the key field."""
        return self.fields[self.key_field_name]  # type: ignore

    @cached_property
    def vector_fields(self) -> list[str]:
        """Get the names of the vector fields."""
        return [name for name, value in self.fields.items() if isinstance(value, VectorStoreRecordVectorField)]

    def __post_init__(self):
        """Validate the fields.

        Raises:
            DataModelException: If a field does not have a name.
            DataModelException: If there is a field with an embedding property name but no corresponding vector field.
            DataModelException: If there is no key field.

        """
        for name, value in self.fields.items():
            if name is None:
                raise VectorStoreModelException("Fields must have a name.")
            if value.name is None:
                value.name = name
            if isinstance(value, VectorStoreRecordDataField) and value.embedding_property_name not in self.field_names:
                raise VectorStoreModelException(
                    "Data field with embedding property name must refer to a existing vector field."
                )
            if isinstance(value, VectorStoreRecordKeyField):
                self.key_field_name = name
        if not self.key_field_name:
            raise VectorStoreModelException("Memory record definition must have a key field.")
