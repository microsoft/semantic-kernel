# Copyright (c) Microsoft. All rights reserved.

from abc import ABC
from dataclasses import dataclass
from functools import cached_property


@dataclass
class Field(ABC):
    name: str | None = None


@dataclass
class MemoryRecordKeyField(Field):
    """Memory record key field."""

    name: str = "key"


@dataclass
class MemoryRecordDataField(Field):
    """Memory record data field."""

    has_embedding: bool = False
    embedding_property_name: str | None = None


@dataclass
class MemoryRecordVectorField(Field):
    """Memory record vector field."""


@dataclass
class MemoryRecordDefinition:
    """Memory record definition."""

    fields: list[Field]

    @cached_property
    def field_names(self) -> list[str]:
        """Get the names of the fields."""
        return [field.name for field in self.fields if field.name is not None]

    @cached_property
    def key_field(self) -> MemoryRecordKeyField:
        """Get the key field."""
        for field in self.fields:
            if isinstance(field, MemoryRecordKeyField):
                return field
        raise ValueError("Memory record definition must have a key field.")

    def validate_fields(self):
        """Validate the fields."""
        key_found = False
        for field in self.fields:
            if field.name is None:
                raise ValueError("Fields must have a name.")
            if isinstance(field, MemoryRecordDataField):
                if not field.has_embedding and not field.embedding_property_name:
                    continue
                if field.has_embedding and field.embedding_property_name is None:
                    raise ValueError("Data field with embedding must have an embedding property name.")
                if field.embedding_property_name is not None and not field.has_embedding:
                    raise ValueError("Data field with embedding property name must have embedding flag set.")
                if field.embedding_property_name not in self.field_names:
                    raise ValueError("Data field with embedding property name must have a corresponding vector field.")
            if isinstance(field, MemoryRecordKeyField):
                key_found = True
        if not key_found:
            raise ValueError("Memory record definition must have a key field.")
