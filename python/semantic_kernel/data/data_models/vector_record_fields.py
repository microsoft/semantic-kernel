# Copyright (c) Microsoft. All rights reserved.

from abc import ABC
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
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

    local_embedding: bool = True
    embedding_settings: dict[str, PromptExecutionSettings | dict[str, Any]] = field(default_factory=dict)


@dataclass
class VectorStoreRecordDefinition:
    """Memory record definition."""

    fields: list[VectorStoreRecordField]

    def get_field_by_name(self, name: str) -> VectorStoreRecordField:
        """Get the field by name."""
        for fld in self.fields:
            if fld.name == name:
                return fld
        raise ValueError(f"Field with name '{name}' not found.")

    @cached_property
    def field_names(self) -> list[str]:
        """Get the names of the fields."""
        return [fld.name for fld in self.fields if fld.name is not None]

    @cached_property
    def key_field(self) -> "VectorStoreRecordKeyField":
        """Get the key field."""
        for fld in self.fields:
            if isinstance(fld, VectorStoreRecordKeyField):
                return fld
        raise ValueError("Memory record definition must have a key field.")

    def validate_fields(self):
        """Validate the fields.

        Raises:
            DataModelException: If a field does not have a name.
            DataModelException: If there is a field with an embedding property name but no corresponding vector field.
            DataModelException: If there is no key field.

        """
        key_found = False
        for fld in self.fields:
            if fld.name is None:
                raise DataModelException("Fields must have a name.")
            if isinstance(fld, VectorStoreRecordDataField) and fld.embedding_property_name not in self.field_names:
                raise DataModelException(
                    "Data field with embedding property name must have a corresponding vector field."
                )
            if isinstance(fld, VectorStoreRecordKeyField):
                key_found = True
        if not key_found:
            raise DataModelException("Memory record definition must have a key field.")
