# Copyright (c) Microsoft. All rights reserved.


from inspect import signature

from semantic_kernel.memory.data_model.memory_record_fields import (
    Field,
    MemoryRecordDataField,
    MemoryRecordVectorField,
)


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
    fields = {}
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
            field_type = MemoryRecordDataField(field.name)
        if field_type.name is None or field_type.name != field.name:
            field_type.name = field.name
        fields[field.name] = field_type
    # check if any data fields, that have a vector field defined refers to a existing vector field
    for field in fields.values():
        if isinstance(field, MemoryRecordDataField) and field.has_embedding:
            vector_field_name = field.embedding_property_name
            if vector_field_name not in fields:
                raise ValueError(f"Field {vector_field_name} not found in data model")
            vector_field = fields[vector_field_name]
            if not isinstance(vector_field, MemoryRecordVectorField):
                raise ValueError(f"Field {vector_field_name} is not a vector field")
    setattr(cls, "__sk_data_model_fields__", fields)
    return cls
