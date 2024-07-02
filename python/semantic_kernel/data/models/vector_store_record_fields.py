# Copyright (c) Microsoft. All rights reserved.

from abc import ABC
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

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
    is_filterable: bool | None = None
    property_type: type[T] | None = None


@dataclass
class VectorStoreRecordVectorField(VectorStoreRecordField):
    """Memory record vector field.

    Args:
        local_embedding (bool, optional): Whether to embed the vector locally. Defaults to True.
        embedding_settings (dict[str, PromptExecutionSettings], optional): Embedding settings.
            The key is the name of the embedding service to use, can be multiple ones.
        cast_function (Callable[[list[float]], Any], optional): Cast function.
            Function that takes one argument, if necessary use a lambda or partial to pre-fill arguments.
            This is called with a list of floats, and should be used when
            the vector is not a list of floats, otherwise leave it at None.
    """

    local_embedding: bool = True
    dimensions: int | None = None
    index_kind: str | None = None  # hnsw, flat, etc.
    distance_function: str | None = None  # cosine, dot prod, euclidan
    embedding_settings: dict[str, PromptExecutionSettings] = field(default_factory=dict)
    cast_function: Callable[[list[float]], Any] | None = None


__all__ = [
    "VectorStoreRecordDataField",
    "VectorStoreRecordKeyField",
    "VectorStoreRecordVectorField",
]
