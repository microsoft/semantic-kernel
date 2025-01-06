# Copyright (c) Microsoft. All rights reserved.

import logging
from inspect import Parameter, _empty, signature
from types import MappingProxyType, NoneType
from typing import Any

from semantic_kernel.data.record_definition.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.record_definition.vector_store_record_fields import (
    VectorStoreRecordField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.exceptions import VectorStoreModelException
from semantic_kernel.utils.experimental_decorator import experimental_function

logger = logging.getLogger(__name__)


@experimental_function
def vectorstoremodel(
    cls: Any | None = None,
):
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
        DataModelException: If the class does not implement the serialize and deserialize methods.
        DataModelException: If there are no fields with a VectorStoreRecordField annotation.
        DataModelException: If there are fields with no name.
        DataModelException: If there is no key field.
        DataModelException: If there is a field with an embedding property name but no corresponding vector field.
    """

    def wrap(cls: Any):
        # get fields and annotations
        cls_sig = signature(cls)
        setattr(cls, "__kernel_vectorstoremodel__", True)
        setattr(cls, "__kernel_vectorstoremodel_definition__", _parse_signature_to_definition(cls_sig.parameters))

        return cls

    # See if we're being called as @vectorstoremodel or @vectorstoremodel().
    if cls is None:
        # We're called with parens.
        return wrap

    # We're called as @vectorstoremodel without parens.
    return wrap(cls)


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


def _parse_parameter_to_field(field: Parameter) -> VectorStoreRecordField | None:
    for field_annotation in getattr(field.annotation, "__metadata__", []):
        if isinstance(field_annotation, VectorStoreRecordField):
            return _parse_vector_store_record_field_instance(field_annotation, field)
        if isinstance(field_annotation, type(VectorStoreRecordField)):
            return _parse_vector_store_record_field_class(field_annotation, field)

    # This means there are no annotations or non VectorStoreRecordField annotations
    if field.default is _empty:
        raise VectorStoreModelException(
            "Fields that do not have a VectorStoreRecord* annotation must have a default value."
        )
    logger.debug(
        f'Field "{field.name}" does not have a VectorStoreRecordField annotation, will not be part of the record.'
    )
    return None


def _parse_vector_store_record_field_instance(
    record_field: VectorStoreRecordField, field: Parameter
) -> VectorStoreRecordField:
    if not record_field.name or record_field.name != field.name:
        record_field.name = field.name
    if not record_field.property_type:
        property_type = field.annotation.__origin__
        if (args := getattr(property_type, "__args__", None)) and NoneType in args and len(args) == 2:
            property_type = args[0]
        if hasattr(property_type, "__args__"):
            if isinstance(record_field, VectorStoreRecordVectorField):
                record_field.property_type = property_type.__args__[0].__name__
            elif property_type.__name__ == "list":
                record_field.property_type = f"{property_type.__name__}[{property_type.__args__[0].__name__}]"
            else:
                record_field.property_type = property_type.__name__
        else:
            record_field.property_type = property_type.__name__
    return record_field


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
