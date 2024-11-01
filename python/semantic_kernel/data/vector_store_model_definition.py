# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass, field

from semantic_kernel.data.vector_store_model_protocols import (
    DeserializeProtocol,
    FromDictProtocol,
    SerializeProtocol,
    ToDictProtocol,
)
from semantic_kernel.data.vector_store_record_fields import (
    VectorStoreRecordDataField,
    VectorStoreRecordField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.exceptions.memory_connector_exceptions import VectorStoreModelException


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
    fields: dict[str, VectorStoreRecordField]
    container_mode: bool = False
    to_dict: ToDictProtocol | None = None
    from_dict: FromDictProtocol | None = None
    serialize: SerializeProtocol | None = None
    deserialize: DeserializeProtocol | None = None

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
            if value.name is None:
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
