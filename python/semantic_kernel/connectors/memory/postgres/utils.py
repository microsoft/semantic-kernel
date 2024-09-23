# Copyright (c) Microsoft. All rights reserved.

import asyncio
import contextlib
import re
from typing import Any

from psycopg_pool import ConnectionPool

from semantic_kernel.data.vector_store_record_fields import VectorStoreRecordField


class ConnectionPoolWrapper(ConnectionPool):
    """Wrapper to make sure the connection is closed when the object is deleted."""

    def __del__(self) -> None:
        """Close connection, done when the object is deleted, used when SK creates a client."""
        with contextlib.suppress(Exception):
            asyncio.get_running_loop().create_task(self.close())


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
    print(python_type_str)
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

    # If the type is not found, default to TEXT
    return None


def convert_row_to_dict(row: tuple[Any, ...], fields: list[tuple[str, VectorStoreRecordField]]) -> dict[str, Any]:
    """Convert a row from a PostgreSQL query to a dictionary.

    Uses the field information to map the row values to the corresponding field names.

    Args:
        row: A row from a PostgreSQL query, represented as a tuple.
        fields: A list of tuples, where each tuple contains the field name and field definition.

    Returns:
        A dictionary representation of the row.
    """
    return {field_name: value for (field_name, _), value in zip(fields, row)}
