# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING, Any

from weaviate.classes.config import Configure, Property
from weaviate.classes.query import Filter
from weaviate.collections.classes.config_named_vectors import _NamedVectorConfigCreate
from weaviate.collections.classes.config_vector_index import _VectorIndexConfigCreate
from weaviate.collections.classes.config_vectorizers import VectorDistances

from semantic_kernel.connectors.memory.weaviate.const import TYPE_MAPPER_DATA
from semantic_kernel.data.const import DistanceFunction, IndexKind
from semantic_kernel.data.record_definition import (
    VectorStoreRecordDataField,
    VectorStoreRecordDefinition,
    VectorStoreRecordVectorField,
)
from semantic_kernel.data.text_search import AnyTagsEqualTo, EqualTo
from semantic_kernel.data.vector_search import VectorSearchFilter
from semantic_kernel.exceptions import (
    VectorStoreModelDeserializationException,
)

if TYPE_CHECKING:
    from weaviate.collections.classes.filters import _Filters


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
    vector_list: list[_NamedVectorConfigCreate] = []

    for vector_field in data_model_definition.vector_fields:
        vector_list.append(
            Configure.NamedVectors.none(
                name=vector_field.name,  # type: ignore
                vector_index_config=to_weaviate_vector_index_config(vector_field),
            )
        )
    return vector_list


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


def to_weaviate_vector_distance(distance_function: DistanceFunction | None) -> VectorDistances | None:
    """Convert a distance function to a Weaviate vector distance metric.

    Args:
        distance_function (DistanceFunction | None): The distance function.

    Returns:
        str: The Weaviate vector distance metric name.
    """
    match distance_function:
        case DistanceFunction.COSINE_DISTANCE:
            return VectorDistances.COSINE
        case DistanceFunction.DOT_PROD:
            return VectorDistances.DOT
        case DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE:
            return VectorDistances.L2_SQUARED
        case DistanceFunction.MANHATTAN:
            return VectorDistances.MANHATTAN
        case DistanceFunction.HAMMING:
            return VectorDistances.HAMMING

    raise ValueError(f"Unsupported distance function for Weaviate: {distance_function}")


# region Serialization helpers


def extract_properties_from_dict_record_based_on_data_model_definition(
    record: dict[str, Any],
    data_model_definition: VectorStoreRecordDefinition,
) -> dict[str, list[float]] | list[float]:
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
    named_vectors: bool,
) -> dict[str, Any] | Any | None:
    """Extract Weaviate object vectors from a dictionary record based on the data model definition.

    By default a collection is set to use named vectors, this means that the name of the vector field is
    added before the value, otherwise it is just the value and there can only be one vector in that case.

    The returned object can be used to construct a Weaviate object.

    Args:
        record (dict[str, Any]): The record.
        data_model_definition (VectorStoreRecordDefinition): The data model definition.
        named_vectors (bool): Whether to use named vectors.

    Returns:
        dict[str, Any]: The vectors.
    """
    if named_vectors:
        return {vector.name: record[vector.name] for vector in data_model_definition.vector_fields}
    return record[data_model_definition.vector_fields[0].name] if data_model_definition.vector_fields else None


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
    named_vectors: bool,
) -> dict[str, Any]:
    """Extract vectors from a Weaviate object based on the data model definition.

    Args:
        weaviate_object: The Weaviate object.
        data_model_definition (VectorStoreRecordDefinition): The data model definition.
        named_vectors (bool): Whether the collection uses named vectors.

    Returns:
        dict[str, Any]: The vectors, or None.
    """
    if not weaviate_object.vector:
        return {}
    if named_vectors:
        return {
            vector.name: weaviate_object.vector[vector.name]
            for vector in data_model_definition.vector_fields
            if vector.name in weaviate_object.vector
        }
    vector_field = data_model_definition.vector_fields[0] if data_model_definition.vector_fields else None
    if not vector_field:
        return {}
    return {vector_field.name: weaviate_object.vector["default"]}


# endregion
# region VectorSearch helpers


def create_filter_from_vector_search_filters(filters: VectorSearchFilter | None) -> "_Filters | None":
    """Create a Weaviate filter from a vector search filter."""
    if not filters:
        return None
    weaviate_filters: list["_Filters"] = []
    for filter in filters.filters:
        match filter:
            case EqualTo():
                weaviate_filters.append(Filter.by_property(filter.field_name).equal(filter.value))
            case AnyTagsEqualTo():
                weaviate_filters.append(Filter.by_property(filter.field_name).like(filter.value))
            case _:
                raise ValueError(f"Unsupported filter type: {filter}")
    return Filter.all_of(weaviate_filters) if weaviate_filters else None
