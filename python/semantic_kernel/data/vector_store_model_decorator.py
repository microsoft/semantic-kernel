# Copyright (c) Microsoft. All rights reserved.

import logging
from inspect import _empty, signature
from types import NoneType
from typing import Any

from semantic_kernel.data.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_store_record_fields import VectorStoreRecordField, VectorStoreRecordVectorField
from semantic_kernel.exceptions.memory_connector_exceptions import VectorStoreModelException

logger = logging.getLogger(__name__)


def vectorstoremodel(
    cls: Any | None = None,
):
    """Returns the class as a vector store model.

    This decorator makes a class a vector store model.
    There are three things being checked:
    - The class must have at least one field with a annotation,
        of type VectorStoreRecordKeyField, VectorStoreRecordDataField or VectorStoreRecordVectorField.
    - The class must have exactly one field with the VectorStoreRecordKeyField annotation.

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


def _parse_signature_to_definition(parameters) -> VectorStoreRecordDefinition:
    if len(parameters) == 0:
        raise VectorStoreModelException(
            "There must be at least one field in the datamodel. If you are using this with a @dataclass, "
            "you might have inverted the order of the decorators, the vectorstoremodel decorator should be the top one."
        )
    fields: dict[str, VectorStoreRecordField] = {}
    for field in parameters.values():
        annotation = field.annotation
        # check first if there are any annotations
        if not hasattr(annotation, "__metadata__"):
            if field._default is _empty:
                raise VectorStoreModelException(
                    "Fields that do not have a VectorStoreRecord* annotation must have a default value."
                )
            logger.info(
                f'Field "{field.name}" does not have a VectorStoreRecord* '
                "annotation, will not be part of the record."
            )
            continue
        property_type = annotation.__origin__
        if (args := getattr(property_type, "__args__", None)) and NoneType in args and len(args) == 2:
            property_type = args[0]
        metadata = annotation.__metadata__
        field_type = None
        for item in metadata:
            if isinstance(item, VectorStoreRecordField):
                field_type = item
                if not field_type.name or field_type.name != field.name:
                    field_type.name = field.name
                if not field_type.property_type:
                    if hasattr(property_type, "__args__"):
                        if isinstance(item, VectorStoreRecordVectorField):
                            field_type.property_type = property_type.__args__[0].__name__
                        elif property_type.__name__ == "list":
                            field_type.property_type = f"{property_type.__name__}[{property_type.__args__[0].__name__}]"
                        else:
                            field_type.property_type = property_type.__name__

                    else:
                        field_type.property_type = property_type.__name__
            elif isinstance(item, type(VectorStoreRecordField)):
                if hasattr(property_type, "__args__") and property_type.__name__ == "list":
                    property_type_name = f"{property_type.__name__}[{property_type.__args__[0].__name__}]"
                else:
                    property_type_name = property_type.__name__
                field_type = item(name=field.name, property_type=property_type_name)
        if not field_type:
            if field._default is _empty:
                raise VectorStoreModelException(
                    "Fields that do not have a VectorStoreRecord* annotation must have a default value."
                )
            logger.debug(
                f'Field "{field.name}" does not have a VectorStoreRecordField '
                "annotation, will not be part of the record."
            )
            continue
        # field name is set either when not None or by instantiating a new field
        assert field_type.name is not None  # nosec
        fields[field_type.name] = field_type
    return VectorStoreRecordDefinition(fields=fields)
