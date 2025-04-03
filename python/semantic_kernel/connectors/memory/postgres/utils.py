# Copyright (c) Microsoft. All rights reserved.

import json
import re
from typing import Any

from psycopg_pool import AsyncConnectionPool

from semantic_kernel.data.const import DistanceFunction
from semantic_kernel.data.record_definition import (
    VectorStoreRecordField,
    VectorStoreRecordVectorField,
)


def python_type_to_postgres(python_type_str: str) -> str | None:
    """Convert a string representation of a Python type to a PostgreSQL data type.

    Args:
        python_type_str: The string representation of the Python type (e.g., "int", "List[str]").

    Returns:
        Corresponding PostgreSQL data type as a string, if found. If the type is not found, return None.
    """
    # Basic type mapping from Python types (in string form) to PostgreSQL types
    type_mapping = {
        "str": "TEXT",
        "int": "INTEGER",
        "float": "DOUBLE PRECISION",
        "bool": "BOOLEAN",
        "dict": "JSONB",
        "datetime": "TIMESTAMP",
        "bytes": "BYTEA",
        "NoneType": "NULL",
    }

    # Regular expression to detect lists, e.g., "List[str]" or "List[int]"
    list_pattern = re.compile(r"(?i)List\[(.*)\]")

    # Check if the type is a list
    match = list_pattern.match(python_type_str)
    if match:
        # Extract the inner type of the list and convert it to a PostgreSQL array type
        element_type_str = match.group(1)
        postgres_element_type = python_type_to_postgres(element_type_str)
        return f"{postgres_element_type}[]"

    # Handle basic types
    if python_type_str in type_mapping:
        return type_mapping[python_type_str]

    return None


def convert_row_to_dict(
    row: tuple[Any, ...], fields: list[tuple[str, VectorStoreRecordField | None]]
) -> dict[str, Any]:
    """Convert a row from a PostgreSQL query to a dictionary.

    Uses the field information to map the row values to the corresponding field names.

    Args:
        row: A row from a PostgreSQL query, represented as a tuple.
        fields: A list of tuples, where each tuple contains the field name and field definition.

    Returns:
        A dictionary representation of the row.
    """

    def _convert(v: Any | None, field: VectorStoreRecordField | None) -> Any | None:
        if v is None:
            return None
        if isinstance(field, VectorStoreRecordVectorField) and isinstance(v, str):
            # psycopg returns vector as a string if pgvector is not loaded.
            # If pgvector is registered with the connection, no conversion is required.
            return json.loads(v)
        return v

    return {field_name: _convert(value, field) for (field_name, field), value in zip(fields, row)}


def convert_dict_to_row(record: dict[str, Any], fields: list[tuple[str, VectorStoreRecordField]]) -> tuple[Any, ...]:
    """Convert a dictionary to a row for a PostgreSQL query.

    Args:
        record: A dictionary representing a record.
        fields: A list of tuples, where each tuple contains the field name and field definition.

    Returns:
        A tuple representing the record.
    """

    def _convert(v: Any | None) -> Any | None:
        if isinstance(v, dict):
            # psycopg requires serializing dicts as strings.
            return json.dumps(v)
        return v

    return tuple(_convert(record.get(field.name)) for _, field in fields)


def get_vector_index_ops_str(distance_function: DistanceFunction) -> str:
    """Get the PostgreSQL ops string for creating an index for a given distance function.

    Args:
        distance_function: The distance function the index is created for.

    Returns:
        The PostgreSQL ops string for the given distance function.

    Examples:
        >>> get_vector_index_ops_str(DistanceFunction.COSINE)
        'vector_cosine_ops'
    """
    if distance_function == DistanceFunction.COSINE_DISTANCE:
        return "vector_cosine_ops"
    if distance_function == DistanceFunction.COSINE_SIMILARITY:
        return "vector_cosine_ops"
    if distance_function == DistanceFunction.DOT_PROD:
        return "vector_ip_ops"
    if distance_function == DistanceFunction.EUCLIDEAN_DISTANCE:
        return "vector_l2_ops"
    if distance_function == DistanceFunction.MANHATTAN:
        return "vector_l1_ops"

    raise ValueError(f"Unsupported distance function: {distance_function}")


def get_vector_distance_ops_str(distance_function: DistanceFunction) -> str:
    """Get the PostgreSQL distance operator string for a given distance function.

    Args:
        distance_function: The distance function for which the operator string is needed.

    Note:
        For the COSINE_SIMILARITY and DOT_PROD distance functions,
        there is additional query steps to retrieve the correct distance.
        For dot product, take -1 * inner product, as <#> returns the negative inner product
        since Postgres only supports ASC order index scans on operators
        For cosine similarity, take 1 - cosine distance.

    Returns:
        The PostgreSQL distance operator string for the given distance function.

    Raises:
        ValueError: If the distance function is unsupported.
    """
    if distance_function == DistanceFunction.COSINE_DISTANCE:
        return "<=>"
    if distance_function == DistanceFunction.COSINE_SIMILARITY:
        return "<=>"
    if distance_function == DistanceFunction.DOT_PROD:
        return "<#>"
    if distance_function == DistanceFunction.EUCLIDEAN_DISTANCE:
        return "<->"
    if distance_function == DistanceFunction.MANHATTAN:
        return "<+>"
    raise ValueError(f"Unsupported distance function: {distance_function}")


async def ensure_open(connection_pool: AsyncConnectionPool) -> AsyncConnectionPool:
    """Ensure the connection pool is open.

    It is safe to call open on an already open connection pool.
    Use this wrapper to ensure the connection pool is open before using it.

    Args:
        connection_pool: The connection pool to ensure is open.

    Returns:
        The connection pool, after ensuring it is open
    """
    await connection_pool.open()
    return connection_pool
