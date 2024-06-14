# Copyright (c) Microsoft. All rights reserved.

import logging
from inspect import signature

from semantic_kernel.exceptions.memory_connector_exceptions import DataModelException
from semantic_kernel.memory.data_model.vector_record_fields import VectorStoreRecordDefinition, VectorStoreRecordField
from semantic_kernel.memory.protocols.data_model_serde_protocol import DataModelSerdeProtocol

logger = logging.getLogger(__name__)


def datamodel(
    cls: object | None = None,
):
    """Returns the class as a datamodel.

    This decorator makes a class a data model.
    There are three things being checked:
    - The class must implement the serialize and deserialize methods as defined in the DataModelSerdeProtocol.
    - The class must have at least one field with a VectorStoreRecordField annotation.
    - The class must have one field with the VectorStoreRecordKeyField annotation.

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

    def wrap(cls: object):
        # get fields and annotations
        if not isinstance(cls, DataModelSerdeProtocol):
            raise DataModelException("Data model must implement self.serialize and cls.deserialize methods.")

        fields = []
        cls_sig = signature(cls)
        for field in cls_sig.parameters.values():
            annotation = field.annotation
            if getattr(annotation, "_name", "") == "Optional":
                annotation = annotation.__args__[0]
            if hasattr(annotation, "__metadata__"):
                annotations = annotation.__metadata__
                for annotation in annotations:
                    if isinstance(annotation, VectorStoreRecordField):
                        field_type = annotation
                        break
                    if isinstance(annotation, type(VectorStoreRecordField)):
                        field_type = annotation(name=field.name)
                        break
            else:
                logger.info(
                    f'Field "{field.name}" does not have a VectorStoreRecordField '
                    "annotation, will not be part of the record."
                )
                continue
            if field_type.name is None or field_type.name != field.name:
                field_type.name = field.name
            fields.append(field_type)
        if not fields and len(cls_sig.parameters.values()) > 0:
            raise DataModelException("There must be at least one field with a VectorStoreRecordField annotation.")
        model = VectorStoreRecordDefinition(fields=fields)
        model.validate_fields()

        setattr(cls, "__kernel_data_model__", True)
        setattr(cls, "__kernel_data_model_fields__", model)

        return cls

    # See if we're being called as @datamodel or @datamodel().
    if cls is None:
        # We're called with parens.
        return wrap

    # We're called as @datamodel without parens.
    return wrap(cls)
