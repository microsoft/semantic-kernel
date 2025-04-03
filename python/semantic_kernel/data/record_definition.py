# Copyright (c) Microsoft. All rights reserved.

import logging
from abc import ABC
from collections.abc import Callable, Sequence
from inspect import Parameter, _empty, signature
from types import MappingProxyType, NoneType
from typing import Any, Protocol, TypeVar, runtime_checkable

from pydantic import Field
from pydantic.dataclasses import dataclass

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.data.const import DistanceFunction, IndexKind
from semantic_kernel.exceptions import VectorStoreModelException
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.feature_stage_decorator import experimental

logger = logging.getLogger(__name__)


# region: Fields


@experimental
@dataclass
class VectorStoreRecordField(ABC):
    """Base class for all Vector Store Record Fields."""

    name: str = ""
    property_type: str | None = None


@experimental
@dataclass
class VectorStoreRecordKeyField(VectorStoreRecordField):
    """Memory record key field."""


@experimental
@dataclass
class VectorStoreRecordDataField(VectorStoreRecordField):
    """Memory record data field."""

    has_embedding: bool = False
    embedding_property_name: str | None = None
    is_filterable: bool | None = None
    is_full_text_searchable: bool | None = None


@experimental
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


# region: Protocols


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


@runtime_checkable
class SerializeMethodProtocol(Protocol):
    """Data model serialization protocol.

    This can optionally be implemented to allow single step serialization and deserialization
    for using your data model with a specific datastore.
    """

    def serialize(self, **kwargs: Any) -> Any:
        """Serialize the object to the format required by the data store."""
        ...  # pragma: no cover


@runtime_checkable
class ToDictMethodProtocol(Protocol):
    """Class used internally to check if a model has a to_dict method."""

    def to_dict(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Serialize the object to the format required by the data store."""
        ...  # pragma: no cover


# region: VectorStoreRecordDefinition


@experimental
class VectorStoreRecordDefinition(KernelBaseModel):
    """Memory record definition.

    Args:
        fields: The fields of the record.
        container_mode: Whether the record is in container mode.
        to_dict: The to_dict function, should take a record and return a list of dicts.
        from_dict: The from_dict function, should take a list of dicts and return a record.
        serialize: The serialize function, should take a record and return the type specific to a datastore.
        deserialize: The deserialize function, should take a type specific to a datastore and return a record.

    """

    fields: dict[str, VectorStoreRecordField]
    key_field_name: str = Field(default="", init=False)
    container_mode: bool = False
    to_dict: ToDictFunctionProtocol | None = None
    from_dict: FromDictFunctionProtocol | None = None
    serialize: SerializeFunctionProtocol | None = None
    deserialize: DeserializeFunctionProtocol | None = None

    @property
    def field_names(self) -> list[str]:
        """Get the names of the fields."""
        return list(self.fields.keys())

    @property
    def key_field(self) -> "VectorStoreRecordKeyField":
        """Get the key field."""
        return self.fields[self.key_field_name]  # type: ignore

    @property
    def vector_field_names(self) -> list[str]:
        """Get the names of the vector fields."""
        return [name for name, value in self.fields.items() if isinstance(value, VectorStoreRecordVectorField)]

    @property
    def non_vector_field_names(self) -> list[str]:
        """Get the names of all the non-vector fields."""
        return [name for name, value in self.fields.items() if not isinstance(value, VectorStoreRecordVectorField)]

    def try_get_vector_field(self, field_name: str | None = None) -> VectorStoreRecordVectorField | None:
        """Try to get the vector field.

        If the field_name is None, then the first vector field is returned.
        If no vector fields are present None is returned.

        Args:
            field_name: The field name.

        Returns:
            VectorStoreRecordVectorField | None: The vector field or None.
        """
        if field_name is None:
            if len(self.vector_fields) == 0:
                return None
            return self.vector_fields[0]
        field = self.fields.get(field_name, None)
        if not field:
            raise VectorStoreModelException(f"Field {field_name} not found.")
        if not isinstance(field, VectorStoreRecordVectorField):
            raise VectorStoreModelException(f"Field {field_name} is not a vector field.")
        return field

    def get_field_names(self, include_vector_fields: bool = True, include_key_field: bool = True) -> list[str]:
        """Get the names of the fields.

        Args:
            include_vector_fields: Whether to include vector fields.
            include_key_field: Whether to include the key field.

        Returns:
            list[str]: The names of the fields.
        """
        field_names = self.field_names
        if not include_vector_fields:
            field_names = [name for name in field_names if name not in self.vector_field_names]
        if not include_key_field:
            field_names = [name for name in field_names if name != self.key_field_name]
        return field_names

    @property
    def vector_fields(self) -> list["VectorStoreRecordVectorField"]:
        """Get the names of the vector fields."""
        return [field for field in self.fields.values() if isinstance(field, VectorStoreRecordVectorField)]

    def model_post_init(self, _: Any):
        """Validate the fields.

        Raises:
            DataModelException: If a field does not have a name.
            DataModelException: If there is a field with an embedding property name but no corresponding vector field.
            DataModelException: If there is no key field.
        """
        if len(self.fields) == 0:
            raise VectorStoreModelException(
                "There must be at least one field with a VectorStoreRecordField annotation."
            )
        for name, value in self.fields.items():
            if not name:
                raise VectorStoreModelException("Fields must have a name.")
            if not value.name:
                value.name = name
            if isinstance(value, VectorStoreRecordKeyField):
                if self.key_field_name != "":
                    raise VectorStoreModelException("Memory record definition must have exactly one key field.")
                self.key_field_name = name
        if not self.key_field_name:
            raise VectorStoreModelException("Memory record definition must have exactly one key field.")


# region: Signature parsing functions


def _parse_vector_store_record_field_class(
    field_type: type[VectorStoreRecordField], field: Parameter
) -> VectorStoreRecordField:
    property_type = field.annotation.__origin__
    if (args := getattr(property_type, "__args__", None)) and NoneType in args and len(args) == 2:
        property_type = args[0]
    if hasattr(property_type, "__args__") and property_type.__name__ == "list":
        property_type_name = f"{property_type.__name__}[{property_type.__args__[0].__name__}]"
    else:
        property_type_name = property_type.__name__
    return field_type(name=field.name, property_type=property_type_name)


def _parse_vector_store_record_field_instance(
    record_field: VectorStoreRecordField, field: Parameter
) -> VectorStoreRecordField:
    if not record_field.name or record_field.name != field.name:
        record_field.name = field.name
    if not record_field.property_type and hasattr(field.annotation, "__origin__"):
        property_type = field.annotation.__origin__
        if (args := getattr(property_type, "__args__", None)) and NoneType in args and len(args) == 2:
            property_type = args[0]
        if hasattr(property_type, "__args__"):
            if isinstance(record_field, VectorStoreRecordVectorField):
                # this means a list and we are then interested in the type of the items in the list
                record_field.property_type = property_type.__args__[0].__name__
            elif property_type.__name__ == "list":
                record_field.property_type = f"{property_type.__name__}[{property_type.__args__[0].__name__}]"
            else:
                record_field.property_type = property_type.__name__
        else:
            if isinstance(record_field, VectorStoreRecordVectorField):
                property_type_name = property_type.__name__
                if property_type_name == "ndarray":
                    if record_field.serialize_function is None:
                        raise VectorStoreModelException(
                            "When using a numpy array as a property type, a serialize function must be provided."
                            "usually: serialize_function=np.ndarray.tolist"
                        )
                    if record_field.deserialize_function is None:
                        raise VectorStoreModelException(
                            "When using a numpy array as a property type, a deserialize function must be provided."
                            "usually: deserialize_function=np.array"
                        )
                else:
                    logger.warning(
                        "Usually the property type of a VectorStoreRecordVectorField "
                        "is a list of numbers or a numpy array."
                    )
            record_field.property_type = property_type.__name__
    return record_field


def _parse_parameter_to_field(field: Parameter) -> VectorStoreRecordField | None:
    # first check if there are any annotations
    if field.annotation is not _empty and hasattr(field.annotation, "__metadata__"):
        for field_annotation in field.annotation.__metadata__:
            # the first annotations of the right type found is used.
            if isinstance(field_annotation, VectorStoreRecordField):
                return _parse_vector_store_record_field_instance(field_annotation, field)
            if isinstance(field_annotation, type(VectorStoreRecordField)):
                return _parse_vector_store_record_field_class(field_annotation, field)
    # This means there are no annotations or that all annotations are of other types.
    # we will check if there is a default, otherwise this will cause a runtime error.
    # because it will not be stored, and retrieving this object will fail without a default for this field.
    if field.default is _empty:
        raise VectorStoreModelException(
            "Fields that do not have a VectorStoreRecordField annotation must have a default value."
        )
    logger.debug(
        f'Field "{field.name}" does not have a VectorStoreRecordField annotation, will not be part of the record.'
    )
    return None


def _parse_signature_to_definition(parameters: MappingProxyType[str, Parameter]) -> VectorStoreRecordDefinition:
    if len(parameters) == 0:
        raise VectorStoreModelException(
            "There must be at least one field in the datamodel. If you are using this with a @dataclass, "
            "you might have inverted the order of the decorators, the vectorstoremodel decorator should be the top one."
        )
    return VectorStoreRecordDefinition(
        fields={
            field.name: field for field in [_parse_parameter_to_field(field) for field in parameters.values()] if field
        }
    )


# region: VectorStoreModel decorator


_T = TypeVar("_T")


@experimental
def vectorstoremodel(
    cls: type[_T] | None = None,
) -> type[_T]:
    """Returns the class as a vector store model.

    This decorator makes a class a vector store model.
    There are three things being checked:
    - The class must have at least one field with a annotation,
        of type VectorStoreRecordKeyField, VectorStoreRecordDataField or VectorStoreRecordVectorField.
    - The class must have exactly one field with the VectorStoreRecordKeyField annotation.
    - A field with multiple VectorStoreRecordKeyField annotations will be set to the first one found.

    Optionally, when there are VectorStoreRecordDataFields that specify a embedding property name,
    there must be a corresponding VectorStoreRecordVectorField with the same name.

    Args:
        cls: The class to be decorated.

    Raises:
        VectorStoreModelException: If the class does not implement the serialize and deserialize methods.
        VectorStoreModelException: If there are no fields with a VectorStoreRecordField annotation.
        VectorStoreModelException: If there are fields with no name.
        VectorStoreModelException: If there is no key field.
        VectorStoreModelException: If there is a field with an embedding property name but no corresponding field.
        VectorStoreModelException: If there is a ndarray field without a serialize or deserialize function.
    """

    def wrap(cls: type[_T]) -> type[_T]:
        # get fields and annotations
        cls_sig = signature(cls)
        setattr(cls, "__kernel_vectorstoremodel__", True)
        setattr(cls, "__kernel_vectorstoremodel_definition__", _parse_signature_to_definition(cls_sig.parameters))

        return cls  # type: ignore

    # See if we're being called as @vectorstoremodel or @vectorstoremodel().
    if cls is None:
        # We're called with parens.
        return wrap  # type: ignore

    # We're called as @vectorstoremodel without parens.
    return wrap(cls)
