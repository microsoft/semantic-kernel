# Copyright (c) Microsoft. All rights reserved.

import logging
from inspect import signature

from semantic_kernel.memory.data_model.memory_record_fields import (
    Field,
    MemoryRecordDefinition,
)

logger = logging.getLogger(__name__)


def datamodel(
    cls=None,
):
    """Returns the class as a datamodel."""

    def wrap(cls):
        # get fields and annotations
        return _parse_cls(cls)

    # See if we're being called as @dataclass or @dataclass().
    if cls is None:
        # We're called with parens.
        return wrap

    # We're called as @dataclass without parens.
    return wrap(cls)


def _parse_cls(cls):
    # get fields and annotations
    setattr(cls, "__sk_data_model__", True)
    fields = []
    cls_sig = signature(cls)
    for field in cls_sig.parameters.values():
        annotation = field.annotation
        if getattr(annotation, "_name", "") == "Optional":
            annotation = annotation.__args__[0]
        if hasattr(annotation, "__metadata__"):
            annotations = annotation.__metadata__
            for annotation in annotations:
                if isinstance(annotation, Field):
                    field_type = annotation
                    break
                if isinstance(annotation, type(Field)):
                    field_type = annotation(name=field.name)
                    break
        else:
            logger.info('Field "%s" does not have a Field annotation, will not be part of the record.', field.name)
        if field_type.name is None or field_type.name != field.name:
            field_type.name = field.name
        fields.append(field_type)
    model = MemoryRecordDefinition(fields=fields)
    model.validate_fields()
    setattr(cls, "__sk_data_model_fields__", model)
    return cls
