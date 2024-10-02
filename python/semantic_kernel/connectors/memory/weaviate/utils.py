# Copyright (c) Microsoft. All rights reserved.

from weaviate.classes.config import Property

from semantic_kernel.connectors.memory.weaviate.const import TYPE_MAPPER_DATA
from semantic_kernel.data.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_store_record_fields import VectorStoreRecordDataField


def data_model_definition_to_weaviate_properties(
    data_model_definition: VectorStoreRecordDefinition,
) -> list[Property]:
    """Convert a data model definition to Weaviate properties.

    Args:
        data_model_definition (VectorStoreRecordDefinition): The data model definition.

    Returns:
        list[Property]: The Weaviate properties.
    """
    properties: list[Property] = []

    for field in data_model_definition.fields.values():
        if isinstance(field, VectorStoreRecordDataField):
            properties.append(
                Property(
                    name=field.name,
                    data_type=TYPE_MAPPER_DATA[field.property_type or "default"],
                )
            )

    return properties
