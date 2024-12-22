# Copyright (c) Microsoft. All rights reserved.

from abc import ABC
from collections.abc import Callable
from typing import Any

from pydantic import Field
from pydantic.dataclasses import dataclass

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.data import DistanceFunction, IndexKind
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
@dataclass
class VectorStoreRecordField(ABC):
    """Base class for all Vector Store Record Fields."""

    name: str = ""
    property_type: str | None = None


@experimental_class
@dataclass
class VectorStoreRecordKeyField(VectorStoreRecordField):
    """Memory record key field."""


@experimental_class
@dataclass
class VectorStoreRecordDataField(VectorStoreRecordField):
    """Memory record data field."""

    has_embedding: bool = False
    embedding_property_name: str | None = None
    is_filterable: bool | None = None
    is_full_text_searchable: bool | None = None


@experimental_class
@dataclass
class VectorStoreRecordVectorField(VectorStoreRecordField):
    """Memory record vector field.

    Most vectors stores use a `list[float]` as the data type for vectors.
    This is the default and all vector stores in SK use this internally.
    But in your class you may want to use a numpy array or some other optimized type,
    in order to support that,
    you can set the deserialize_function to a function that takes a list of floats and returns the optimized type,
    and then also supply a serialize_function that takes the optimized type and returns a list of floats.

    For instance for numpy, that would be `serialize_function=np.ndarray.tolist` and `deserialize_function=np.array`,
    (with `import numpy as np` at the top of your file).
    if you want to set it up with more specific options, use a lambda, a custom function or a partial.

    Args:
        property_type (str, optional): Property type.
            For vectors this should be the inner type of the vector.
            By default the vector will be a list of numbers.
            If you want to use a numpy array or some other optimized format,
            set the cast_function with a function
            that takes a list of floats and returns a numpy array.
        local_embedding (bool, optional): Whether to embed the vector locally. Defaults to True.
        embedding_settings (dict[str, PromptExecutionSettings], optional): Embedding settings.
            The key is the name of the embedding service to use, can be multiple ones.
        serialize_function (Callable[[Any], list[float | int]], optional): Serialize function,
            should take the vector and return a list of numbers.
        deserialize_function (Callable[[list[float | int]], Any], optional): Deserialize function,
            should take a list of numbers and return the vector.
    """

    local_embedding: bool = True
    dimensions: int | None = None
    index_kind: IndexKind | None = None
    distance_function: DistanceFunction | None = None
    embedding_settings: dict[str, PromptExecutionSettings] = Field(default_factory=dict)
    serialize_function: Callable[[Any], list[float | int]] | None = None
    deserialize_function: Callable[[list[float | int]], Any] | None = None


__all__ = [
    "VectorStoreRecordDataField",
    "VectorStoreRecordKeyField",
    "VectorStoreRecordVectorField",
]
