# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Protocol, TypeVar, runtime_checkable

TModel = TypeVar("TModel", bound=object)


@runtime_checkable
class DataModelSerdeProtocol(Protocol):
    """Data model serialization and deserialization protocol.

    Will be checked against the data model provided by the datamodel decorator.
    """

    def serialize(self) -> dict[str, Any]:
        """Serialize the object to a dictionary."""
        ...

    @classmethod
    def deserialize(cls: type[TModel], obj: dict[str, Any]) -> TModel:
        """Deserialize a dictionary to an object."""
        ...
