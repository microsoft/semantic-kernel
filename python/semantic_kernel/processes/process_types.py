# Copyright (c) Microsoft. All rights reserved.

import types
from typing import Any, TypeVar, Union, get_args, get_origin, get_type_hints

from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep
from semantic_kernel.utils.feature_stage_decorator import experimental

TStep = TypeVar("TStep", bound=KernelProcessStep)
TState = TypeVar("TState")


@experimental
def get_generic_state_type(cls) -> Any:
    """Given a subclass of KernelProcessStep, retrieve the concrete type of 'state'."""
    try:
        type_hints = get_type_hints(cls)
        t_state = type_hints.get("state", None)
        if t_state is not None:
            # Handle Union types and Python 3.12 '|' syntax explicitly
            origin = get_origin(t_state)
            if origin in {Union, types.UnionType}:
                args = get_args(t_state)
                # Filter out 'NoneType' and keep the remaining types
                non_none_args = [arg for arg in args if arg is not type(None)]
                t_state = non_none_args[0] if non_none_args else None
            # Check if t_state is a TypeVar (e.g., TypeVar('TState'))
            if isinstance(t_state, TypeVar):
                t_state = None  # We don't have a concrete type
            return t_state
    except Exception:
        pass  # nosec
    # Recursively check base classes
    for base in cls.__bases__:
        t_state = get_generic_state_type(base)
        if t_state is not None:
            return t_state
    return None
