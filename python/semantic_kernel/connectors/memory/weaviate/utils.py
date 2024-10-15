# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from weaviate.classes.config import Configure, Property
from weaviate.collections.classes.config_named_vectors import _NamedVectorConfigCreate
from weaviate.collections.classes.config_vector_index import _VectorIndexConfigCreate

from semantic_kernel.connectors.memory.weaviate.const import TYPE_MAPPER_DATA
from semantic_kernel.data.const import DistanceFunction, IndexKind
from semantic_kernel.data.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_store_record_fields import VectorStoreRecordDataField, VectorStoreRecordVectorField
from semantic_kernel.exceptions.memory_connector_exceptions import VectorStoreModelDeserializationException


def data_model_definition_to_weaviate_properties(
    data_model_definition: VectorStoreRecordDefinition,
) -> list[Property]:
    """Convert vector store data fields to Weaviate properties.

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
                    index_filterable=field.is_filterable,
                    index_full_text=field.is_full_text_searchable,
                )
            )

    return properties


def data_model_definition_to_weaviate_named_vectors(
    data_model_definition: VectorStoreRecordDefinition,
) -> list[_NamedVectorConfigCreate]:
    """Convert vector store vector fields to Weaviate named vectors.

    Args:
        data_model_definition (VectorStoreRecordDefinition): The data model definition.

    Returns:
        list[_NamedVectorConfigCreate]: The Weaviate named vectors.
    """
    named_vectors: list[_NamedVectorConfigCreate] = []

    for vector in data_model_definition.fields.values():
        if isinstance(vector, VectorStoreRecordVectorField):
            named_vectors.append(
                Configure.NamedVectors.none(
                    name=vector.name,
                    vector_index_config=to_weaviate_vector_index_config(vector),
                )
            )

    return named_vectors


def to_weaviate_vector_index_config(vector: VectorStoreRecordVectorField) -> _VectorIndexConfigCreate:
    """Convert a vector field to a Weaviate vector index configuration.

    Args:
        vector (VectorStoreRecordVectorField): The vector field.

    Returns:
        The Weaviate vector index configuration.
    """
    if vector.index_kind == IndexKind.HNSW:
        return Configure.VectorIndex.hnsw(
            distance_metric=to_weaviate_vector_distance(vector.distance_function),
        )
    if vector.index_kind == IndexKind.FLAT:
        return Configure.VectorIndex.flat(
            distance_metric=to_weaviate_vector_distance(vector.distance_function),
        )

    return Configure.VectorIndex.none()


def to_weaviate_vector_distance(distance_function: DistanceFunction | None) -> str | None:
    """Convert a distance function to a Weaviate vector distance metric.

    Args:
        distance_function (DistanceFunction | None): The distance function.

    Returns:
        str: The Weaviate vector distance metric name.
    """
    match distance_function:
        case DistanceFunction.COSINE:
            return "cosine"
        case DistanceFunction.DOT_PROD:
            return "dot"
        case DistanceFunction.EUCLIDEAN:
            return "l2-squared"
        case DistanceFunction.MANHATTAN:
            return "manhattan"
        case DistanceFunction.HAMMING:
            return "hamming"

    return None


# region Serialization helpers


def extract_properties_from_dict_record_based_on_data_model_definition(
    record: dict[str, Any],
    data_model_definition: VectorStoreRecordDefinition,
) -> dict[str, Any]:
    """Extract Weaviate object properties from a dictionary record based on the data model definition.

    Expecting the record to have all the  data fields defined in the data model definition.

    The returned object can be used to construct a Weaviate object.

    Args:
        record (dict[str, Any]): The record.
        data_model_definition (VectorStoreRecordDefinition): The data model definition.

    Returns:
        dict[str, Any]: The extra properties.
    """
    return {
        field.name: record[field.name]
        for field in data_model_definition.fields.values()
        if isinstance(field, VectorStoreRecordDataField) and field.name
    }


def extract_key_from_dict_record_based_on_data_model_definition(
    record: dict[str, Any],
    data_model_definition: VectorStoreRecordDefinition,
) -> str | None:
    """Extract Weaviate object key from a dictionary record based on the data model definition.

    Expecting the record to have a key field defined in the data model definition.

    The returned object can be used to construct a Weaviate object.
    The key maps to a Weaviate object ID.

    Args:
        record (dict[str, Any]): The record.
        data_model_definition (VectorStoreRecordDefinition): The data model definition.

    Returns:
        str: The key.
    """
    return record[data_model_definition.key_field.name] if data_model_definition.key_field.name else None


def extract_vectors_from_dict_record_based_on_data_model_definition(
    record: dict[str, Any],
    data_model_definition: VectorStoreRecordDefinition,
) -> dict[str, Any]:
    """Extract Weaviate object vectors from a dictionary record based on the data model definition.

    Named vectors will use the names of the associated data fields when possible. If a vector field does not have
    an associated data field, the vector will use its own name. If a vector field does not have a name, the vector will
    not be extracted.

    Expecting the record to have all the vector fields defined in the data model definition.

    The returned object can be used to construct a Weaviate object.

    Args:
        record (dict[str, Any]): The record.
        data_model_definition (VectorStoreRecordDefinition): The data model definition.

    Returns:
        dict[str, Any]: The vectors.
    """
    # Named vectors: key is the data field name, value is the vector field name
    named_vectors: dict[str, str] = {
        field.name: field.embedding_property_name
        for field in data_model_definition.fields.values()
        if isinstance(field, VectorStoreRecordDataField) and field.has_embedding
    }
    # Unnamed vectors: a list of vector fields that are not associated with a data field
    unnamed_vectors: list[str] = [
        field.name
        for field in data_model_definition.fields.values()
        if isinstance(field, VectorStoreRecordVectorField)
        and not field.name
        and field.name not in named_vectors.values()
    ]

    # Combine named and unnamed vectors: Unnamed vectors will use their own names
    vectors: dict[str, str] = named_vectors | {vector_name: vector_name for vector_name in unnamed_vectors}

    return {data_field_name: record[vector_field_name] for data_field_name, vector_field_name in vectors.items()}


# endregion

# region Deserialization helpers


def extract_properties_from_weaviate_object_based_on_data_model_definition(
    weaviate_object,
    data_model_definition: VectorStoreRecordDefinition,
) -> dict[str, Any]:
    """Extract data model properties from a Weaviate object based on the data model definition.

    Expecting the Weaviate object to have all the properties defined in the data model definition.

    Args:
        weaviate_object: The Weaviate object.
        data_model_definition (VectorStoreRecordDefinition): The data model definition.

    Returns:
        dict[str, Any]: The data model properties.
    """
    return {
        field.name: weaviate_object.properties[field.name]
        for field in data_model_definition.fields.values()
        if isinstance(field, VectorStoreRecordDataField) and field.name in weaviate_object.properties
    }


def extract_key_from_weaviate_object_based_on_data_model_definition(
    weaviate_object,
    data_model_definition: VectorStoreRecordDefinition,
) -> dict[str, str]:
    """Extract data model key from a Weaviate object based on the data model definition.

    Expecting the Weaviate object to have an id defined.

    Args:
        weaviate_object: The Weaviate object.
        data_model_definition (VectorStoreRecordDefinition): The data model definition.

    Returns:
        str: The key.
    """
    if data_model_definition.key_field.name and weaviate_object.uuid:
        return {data_model_definition.key_field.name: weaviate_object.uuid}

    # This is not supposed to happen
    raise VectorStoreModelDeserializationException("Unable to extract id/key from Weaviate store model")


def extract_vectors_from_weaviate_object_based_on_data_model_definition(
    weaviate_object,
    data_model_definition: VectorStoreRecordDefinition,
) -> dict[str, Any]:
    """Extract vectors from a Weaviate object based on the data model definition.

    Named vectors use the names of the associated data fields.
    Rest of the vectors use their own names.

    Expecting the Weaviate object to have all the vectors defined in the data model definition.

    Args:
        weaviate_object: The Weaviate object.
        data_model_definition (VectorStoreRecordDefinition): The data model definition.

    Returns:
        dict[str, Any]: The vectors.
    """
    # Named vectors: key is the data field name, value is the vector field name
    named_vectors: dict[str, str] = {
        field.name: field.embedding_property_name
        for field in data_model_definition.fields.values()
        if isinstance(field, VectorStoreRecordDataField) and field.has_embedding
    }
    # Unnamed vectors: a list of vector fields that are not associated with a data field
    unnamed_vectors: list[str] = [
        field.name
        for field in data_model_definition.fields.values()
        if isinstance(field, VectorStoreRecordVectorField)
        and not field.name
        and field.name not in named_vectors.values()
    ]

    # Combine named and unnamed vectors: Unnamed vectors will use their own names
    vectors: dict[str, str] = named_vectors | {vector_name: vector_name for vector_name in unnamed_vectors}

    return {
        vector_field_name: weaviate_object.vector[data_field_name]
        for data_field_name, vector_field_name in vectors.items()
    }


# endregion
