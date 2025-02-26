# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Sequence
from typing import Any, Protocol, TypeVar, runtime_checkable

from semantic_kernel.utils.feature_stage_decorator import experimental

TModel = TypeVar("TModel", bound=object)


@experimental
@runtime_checkable
class SerializeMethodProtocol(Protocol):
    """Data model serialization protocol.

    This can optionally be implemented to allow single step serialization and deserialization
    for using your data model with a specific datastore.
    """

    def serialize(self, **kwargs: Any) -> Any:
        """Serialize the object to the format required by the data store."""
        ...  # pragma: no cover


@experimental
@runtime_checkable
class ToDictMethodProtocol(Protocol):
    """Class used internally to check if a model has a to_dict method."""

    def to_dict(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Serialize the object to the format required by the data store."""
        ...  # pragma: no cover


@experimental
@runtime_checkable
class ToDictFunctionProtocol(Protocol):
    """Protocol for to_dict function.

    Args:
        record: The record to be serialized.
        **kwargs: Additional keyword arguments.

    Returns:
        A list of dictionaries.
    """

    def __call__(self, record: Any, **kwargs: Any) -> Sequence[dict[str, Any]]: ...  # pragma: no cover  # noqa: D102


@experimental
@runtime_checkable
class FromDictFunctionProtocol(Protocol):
    """Protocol for from_dict function.

    Args:
        records: A list of dictionaries.
        **kwargs: Additional keyword arguments.

    Returns:
        A record or list thereof.
    """

    def __call__(self, records: Sequence[dict[str, Any]], **kwargs: Any) -> Any: ...  # noqa: D102


@experimental
@runtime_checkable
class SerializeFunctionProtocol(Protocol):
    """Protocol for serialize function.

    Args:
        record: The record to be serialized.
        **kwargs: Additional keyword arguments.

    Returns:
        The serialized record, ready to be consumed by the specific store.

    """

    def __call__(self, record: Any, **kwargs: Any) -> Any: ...  # noqa: D102


@experimental
@runtime_checkable
class DeserializeFunctionProtocol(Protocol):
    """Protocol for deserialize function.

    Args:
        records: The serialized record directly from the store.
        **kwargs: Additional keyword arguments.

    Returns:
        The deserialized record in the format expected by the application.

    """

    def __call__(self, records: Any, **kwargs: Any) -> Any: ...  # noqa: D102
