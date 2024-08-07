# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Sequence
from typing import Any, Protocol, TypeVar, runtime_checkable

TModel = TypeVar("TModel", bound=object)


@runtime_checkable
class VectorStoreModelFunctionSerdeProtocol(Protocol):
    """Data model serialization and deserialization protocol.

    This can optionally be implemented to allow single step serialization and deserialization
    for using your data model with a specific datastore.
    """

    def serialize(self, **kwargs: Any) -> Any:
        """Serialize the object to the format required by the data store."""
        ...  # pragma: no cover

    @classmethod
    def deserialize(cls: type[TModel], obj: Any, **kwargs: Any) -> TModel:
        """Deserialize the output of the data store to an object."""
        ...  # pragma: no cover


@runtime_checkable
class VectorStoreModelPydanticProtocol(Protocol):
    """Class used internally to make sure a datamodel has model_dump and model_validate."""

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Serialize the object to the format required by the data store."""
        ...  # pragma: no cover

    @classmethod
    def model_validate(cls: type[TModel], *args: Any, **kwargs: Any) -> TModel:
        """Deserialize the output of the data store to an object."""
        ...  # pragma: no cover


@runtime_checkable
class VectorStoreModelToDictFromDictProtocol(Protocol):
    """Class used internally to check if a model has to_dict and from_dict methods."""

    def to_dict(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Serialize the object to the format required by the data store."""
        ...  # pragma: no cover

    @classmethod
    def from_dict(cls: type[TModel], *args: Any, **kwargs: Any) -> TModel:
        """Deserialize the output of the data store to an object."""
        ...  # pragma: no cover


@runtime_checkable
class ToDictProtocol(Protocol):
    """Protocol for to_dict method.

    Args:
        record: The record to be serialized.
        **kwargs: Additional keyword arguments.

    Returns:
        A list of dictionaries.
    """

    def __call__(self, record: Any, **kwargs: Any) -> Sequence[dict[str, Any]]: ...  # pragma: no cover  # noqa: D102


@runtime_checkable
class FromDictProtocol(Protocol):
    """Protocol for from_dict method.

    Args:
        records: A list of dictionaries.
        **kwargs: Additional keyword arguments.

    Returns:
        A record or list thereof.
    """

    def __call__(self, records: Sequence[dict[str, Any]], **kwargs: Any) -> Any: ...  # noqa: D102


@runtime_checkable
class SerializeProtocol(Protocol):
    """Protocol for serialize method.

    Args:
        record: The record to be serialized.
        **kwargs: Additional keyword arguments.

    Returns:
        The serialized record, ready to be consumed by the specific store.

    """

    def __call__(self, record: Any, **kwargs: Any) -> Any: ...  # noqa: D102


@runtime_checkable
class DeserializeProtocol(Protocol):
    """Protocol for deserialize method.

    Args:
        records: The serialized record directly from the store.
        **kwargs: Additional keyword arguments.

    Returns:
        The deserialized record in the format expected by the application.

    """

    def __call__(self, records: Any, **kwargs: Any) -> Any: ...  # noqa: D102
