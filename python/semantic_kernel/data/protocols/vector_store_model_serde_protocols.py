# Copyright (c) Microsoft. All rights reserved.

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
        ...

    @classmethod
    def deserialize(cls: type[TModel], obj: Any, **kwargs: Any) -> TModel:
        """Deserialize the output of the data store to an object."""
        ...


@runtime_checkable
class VectorStoreModelPydanticProtocol(Protocol):
    """Class used internally to make sure a datamodel has model_dump and model_validate."""

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Serialize the object to the format required by the data store."""
        ...

    @classmethod
    def model_validate(cls: type[TModel], *args: Any, **kwargs: Any) -> TModel:
        """Deserialize the output of the data store to an object."""
        ...


@runtime_checkable
class VectorStoreModelToDictFromDictProtocol(Protocol):
    """Class used internally to check if a model has to_dict and from_dict methods."""

    def to_dict(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Serialize the object to the format required by the data store."""
        ...

    @classmethod
    def from_dict(cls: type[TModel], *args: Any, **kwargs: Any) -> TModel:
        """Deserialize the output of the data store to an object."""
        ...
