# Copyright (c) Microsoft. All rights reserved.

from abc import ABC
from dataclasses import dataclass
from functools import cached_property

from semantic_kernel.exceptions.memory_connector_exceptions import DataModelException


@dataclass
class VectorStoreRecordField(ABC):
    name: str | None = None


@dataclass
class VectorStoreRecordKeyField(VectorStoreRecordField):
    """Memory record key field."""

    name: str = "key"


@dataclass
class VectorStoreRecordDataField(VectorStoreRecordField):
    """Memory record data field."""

    has_embedding: bool = False
    embedding_property_name: str | None = None


@dataclass
class VectorStoreRecordVectorField(VectorStoreRecordField):
    """Memory record vector field."""


@dataclass
class VectorStoreRecordDefinition:
    """Memory record definition."""

    fields: list[VectorStoreRecordField]

    @cached_property
    def field_names(self) -> list[str]:
        """Get the names of the fields."""
        return [field.name for field in self.fields if field.name is not None]

    @cached_property
    def key_field(self) -> "VectorStoreRecordKeyField":
        """Get the key field."""
        for field in self.fields:
            if isinstance(field, VectorStoreRecordKeyField):
                return field
        raise ValueError("Memory record definition must have a key field.")

    def validate_fields(self):
        """Validate the fields.

        Raises:
            DataModelException: If a field does not have a name.
            DataModelException: If there is a field with an embedding property name but no corresponding vector field.
            DataModelException: If there is no key field.

        """
        key_found = False
        for field in self.fields:
            if field.name is None:
                raise DataModelException("Fields must have a name.")
            if isinstance(field, VectorStoreRecordDataField) and field.embedding_property_name not in self.field_names:
                raise DataModelException(
                    "Data field with embedding property name must have a corresponding vector field."
                )
            if isinstance(field, VectorStoreRecordKeyField):
                key_found = True
        if not key_found:
            raise DataModelException("Memory record definition must have a key field.")
