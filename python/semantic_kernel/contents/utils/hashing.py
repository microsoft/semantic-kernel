# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from pydantic import BaseModel


def make_hashable(input: Any, visited=None) -> Any:
    """Recursively convert unhashable types to hashable equivalents.

    Args:
        input: The input to convert to a hashable type.
        visited: A dictionary of visited objects to prevent infinite recursion.

    Returns:
        Any: The input converted to a hashable type.
    """
    if visited is None:
        visited = {}

    # If we've seen this object before, return the stored placeholder or final result
    unique_obj_id = id(input)
    if unique_obj_id in visited:
        return visited[unique_obj_id]

    # Handle Pydantic models by manually traversing fields
    if isinstance(input, BaseModel):
        visited[unique_obj_id] = None
        data = {}
        for field_name in input.model_fields:
            value = getattr(input, field_name)
            data[field_name] = make_hashable(value, visited)
        result = tuple(sorted(data.items()))
        visited[unique_obj_id] = result
        return result

    # Convert dictionaries
    if isinstance(input, dict):
        visited[unique_obj_id] = None
        items = tuple(sorted((k, make_hashable(v, visited)) for k, v in input.items()))
        visited[unique_obj_id] = items
        return items

    # Convert lists, sets, and tuples to tuples
    if isinstance(input, (list, set, tuple)):
        visited[unique_obj_id] = None
        items = tuple(make_hashable(item, visited) for item in input)
        visited[unique_obj_id] = items
        return items

    # If it's already something hashable, just return it
    return input
