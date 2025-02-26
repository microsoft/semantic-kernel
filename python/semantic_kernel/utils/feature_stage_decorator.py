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


@release_candidate()
class MyRCClass:
    '''A class that is nearly final, but still in release-candidate stage.
    
    Uses the DEFAULT_RC_VERSION specified in the __init__.py file.
    '''
    pass
    
@release_candidate("1.22.0-rc2")
class MyRCClass:
    '''A class that is nearly final, but still in release-candidate stage.
    
    Uses the specified version as part of the decorator
    '''
    pass
"""


def stage(status: str = "experimental", version: str | None = None) -> Callable[[Callable | T], Callable | T]:
    """Decorator to mark a function or a class with a specific development stage.

    Args:
        status: The development stage, for example, 'experimental', 'release_candidate', 'ga'.
        version: Optional version or release info, e.g. '1.22.0-rc1'.

    Returns:
        The decorated function/class with updated docstring and metadata.
    """

    def decorator(obj: Callable | T) -> Callable | T:
        entity_type = "class" if isinstance(obj, type) else "function"
        version_string = f" (Version: {version})" if version else ""
        note = f"Note: This {entity_type} is '{status}'{version_string} and may change in the future."

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
    """A convenience decorator specifically for features in the 'experimental' stage."""
    return stage(status="experimental")(obj)


def release_candidate(version: str | None = None) -> Callable[[Callable | T], Callable | T]:
    """A convenience decorator specifically for features in the 'release candidate' stage.

    Args:
        version: A specific RC version (defaults to DEFAULT_RC_VERSION).

    Returns:
        The decorated function/class with updated docstring and metadata.
    """
    from semantic_kernel import DEFAULT_RC_VERSION

    rc_version = version if version else DEFAULT_RC_VERSION

    def wrapper(obj: Callable | T) -> Callable | T:
        return stage(status="release_candidate", version=rc_version)(obj)

    return wrapper
