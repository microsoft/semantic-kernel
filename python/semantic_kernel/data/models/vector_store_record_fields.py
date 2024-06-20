# Copyright (c) Microsoft. All rights reserved.

from abc import ABC
from dataclasses import dataclass, field
from typing import TypeVar

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings

T = TypeVar("T")


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
    embedding_settings: dict[str, PromptExecutionSettings] = field(default_factory=dict)


__all__ = [
    "VectorStoreRecordDataField",
    "VectorStoreRecordKeyField",
    "VectorStoreRecordVectorField",
]
