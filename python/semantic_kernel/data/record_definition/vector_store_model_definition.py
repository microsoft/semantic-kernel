# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass, field
from typing import TypeAlias, TypeVar

from semantic_kernel.data.record_definition.vector_store_model_protocols import (
    DeserializeFunctionProtocol,
    FromDictFunctionProtocol,
    SerializeFunctionProtocol,
    ToDictFunctionProtocol,
)
from semantic_kernel.data.record_definition.vector_store_record_fields import (
    VectorStoreRecordDataField,
    VectorStoreRecordField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.exceptions import VectorStoreModelException
from semantic_kernel.utils.feature_stage_decorator import experimental

VectorStoreRecordFields = TypeVar("VectorStoreRecordFields", bound=VectorStoreRecordField)
FieldsType: TypeAlias = dict[str, VectorStoreRecordFields]


@experimental
@dataclass
class VectorStoreRecordDefinition:
    """Memory record definition.

    Args:
        fields: The fields of the record.
        container_mode: Whether the record is in container mode.
        to_dict: The to_dict function, should take a record and return a list of dicts.
        from_dict: The from_dict function, should take a list of dicts and return a record.
        serialize: The serialize function, should take a record and return the type specific to a datastore.
        deserialize: The deserialize function, should take a type specific to a datastore and return a record.

    """

    key_field_name: str = field(init=False)
    fields: FieldsType
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

    def __post_init__(self):
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
        self.key_field_name = ""
        for name, value in self.fields.items():
            if not name:
                raise VectorStoreModelException("Fields must have a name.")
            if not value.name:
                value.name = name
            if (
                isinstance(value, VectorStoreRecordDataField)
                and value.has_embedding
                and value.embedding_property_name not in self.field_names
            ):
                raise VectorStoreModelException(
                    "Data field with embedding property name must refer to a existing vector field."
                )
            if isinstance(value, VectorStoreRecordKeyField):
                if self.key_field_name != "":
                    raise VectorStoreModelException("Memory record definition must have exactly one key field.")
                self.key_field_name = name
        if not self.key_field_name:
            raise VectorStoreModelException("Memory record definition must have exactly one key field.")
