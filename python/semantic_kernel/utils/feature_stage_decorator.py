# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T", bound=type)

"""
# Usage Example:

@experimental
class MyExperimentalClass:
    '''A class that is still evolving rapidly.'''
    pass

@stage(status="experimental")
class MyExperimentalClass:
    '''A class that is still evolving rapidly.'''
    pass

@experimental
def my_experimental_function():
    '''A function that is still evolving rapidly.'''
    pass

@release_candidate
class MyRCClass:
    '''A class that is nearly final, but still in release-candidate stage.
    
    Uses the DEFAULT_RC_VERSION specified in the __init__.py file.
    '''
    pass
    
@release_candidate("1.23.1-rc1")
class MyRCClass:
    '''A class that is nearly final, but still in release-candidate stage.
    
    Uses the specified version as part of the decorator
    '''
    pass
"""


def stage(status: str = "experimental", version: str | None = None) -> Callable[[Callable | T], Callable | T]:
    """A general-purpose decorator for marking a function or a class.

    It is used with a specific development stage. It updates the docstring and
    attaches 'stage_status' (and optionally 'stage_version') as metadata.

    Args:
        status: The development stage, for example 'experimental', 'release_candidate', 'ga', etc.
        version: Optional version or release info (e.g., '1.21.0-rc4').

    Returns:
        A decorator that updates the docstring and metadata of
        the target function/class.
    """

    def decorator(obj: Callable | T) -> Callable | T:
        entity_type = "class" if isinstance(obj, type) else "function"

        version_string = f" (Version: {version})" if version else ""
        note = f"Note: This {entity_type} is marked as '{status}'{version_string} and may change in the future."

        if obj.__doc__:
            obj.__doc__ += f"\n\n{note}"
        else:
            obj.__doc__ = note

        setattr(obj, "stage_status", status)
        if version:
            setattr(obj, "stage_version", version)

        return obj

    return decorator


def experimental(obj: Callable | T) -> Callable | T:
    """Decorator specifically for 'experimental' features.

    It uses the general 'stage' decorator but also attaches 'is_experimental = True'.
    """
    decorated = stage(status="experimental")(obj)
    setattr(decorated, "is_experimental", True)
    return decorated


def release_candidate(
    func: Callable | T | None = None, *, version: str | None = None
) -> Callable[[Callable | T], Callable | T] | Callable | T:
    """Decorator that can be used to mark a function/class as 'release candidate'.

    Supports the following usage patterns:
        1) @release_candidate  (no parentheses)
        2) @release_candidate()  (empty parentheses)
        3) @release_candidate("1.21.3-rc1")  (positional version)
        4) @release_candidate(version="1.21.3-rc1")  (keyword version)

    Args:
        func:
            - In cases (1) or (2), this is the function/class being decorated.
            - In cases (3) or (4), this may be a version string or None.
        version:
            The RC version string, if provided via keyword argument.

    Returns:
        The decorated object, with an updated docstring and attribute
        'is_release_candidate = True'.
    """
    from semantic_kernel import DEFAULT_RC_VERSION

    def _apply(obj: Callable | T, ver: str | None) -> Callable | T:
        decorated = stage(status="release_candidate", version=ver)(obj)
        setattr(decorated, "is_release_candidate", True)
        return decorated

    if callable(func):
        resolved_version = version or DEFAULT_RC_VERSION
        return _apply(func, resolved_version)

    resolved_version = func if isinstance(func, str) else version
    resolved_version = resolved_version or DEFAULT_RC_VERSION

    def wrapper(obj: Callable | T) -> Callable | T:
        return _apply(obj, resolved_version)

    return wrapper
