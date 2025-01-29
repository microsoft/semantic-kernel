# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from pydantic import BaseModel


def make_hashable(input: Any) -> Any:
    """Recursively convert unhashable types to hashable equivalents.

    Args:
        input: The input to convert to a hashable type.

    Returns:
        Any: The input converted to a hashable type.
    """
    if isinstance(input, dict):
        return tuple(sorted((k, make_hashable(v)) for k, v in input.items()))
    if isinstance(input, (list, set, tuple)):
        # Convert lists, sets, and tuples to tuples so they can be hashed
        return tuple(make_hashable(item) for item in input)
    if isinstance(input, BaseModel):
        # If obj is a Pydantic model, convert it to a dict and process
        return make_hashable(input.model_dump())
    return input  # Return the input if it's already hashable
