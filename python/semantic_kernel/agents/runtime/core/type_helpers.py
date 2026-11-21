# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Sequence
from types import NoneType, UnionType
from typing import Any, Optional, Union, get_args, get_origin

from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
def is_union(t: object) -> bool:
    """Check if the type is a Union or UnionType."""
    origin = get_origin(t)
    return origin is Union or origin is UnionType


@experimental
def is_optional(t: object) -> bool:
    """Check if the type is an Optional."""
    origin = get_origin(t)
    return origin is Optional


@experimental
def get_types(t: object) -> Sequence[type[Any]] | None:
    """Get the types from a Union or Optional type."""
    if is_union(t):
        return get_args(t)
    if is_optional(t):
        return tuple([*list(get_args(t)), NoneType])
    if isinstance(t, type):
        return (t,)
    if isinstance(t, NoneType):
        return (NoneType,)
    return None
