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

    key_field_name: str = field(init=False)
    fields: dict[str, VectorStoreRecordField]

    @cached_property
    def field_names(self) -> list[str]:
        """Get the names of the fields."""
        return list(self.fields.keys())

    @property
    def key_field(self) -> "VectorStoreRecordKeyField":
        """Get the key field."""
        return self.fields[self.key_field_name]  # type: ignore

    def __post_init__(self):
        """Validate the fields.

        Raises:
            DataModelException: If a field does not have a name.
            DataModelException: If there is a field with an embedding property name but no corresponding vector field.
            DataModelException: If there is no key field.

        """
        for name, value in self.fields.items():
            if name is None:
                raise DataModelException("Fields must have a name.")
            if isinstance(value, VectorStoreRecordDataField) and value.embedding_property_name not in self.field_names:
                raise DataModelException(
                    "Data field with embedding property name must refer to a existing vector field."
                )
            if isinstance(value, VectorStoreRecordKeyField):
                self.key_field_name = name
        if not self.key_field_name:
            raise DataModelException("Memory record definition must have a key field.")
