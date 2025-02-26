# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

DEFAULT_RC_NOTE = (
    "Features marked with this status are nearing completion and are considered "
    "stable for most purposes, but may still incur minor refinements or "
    "optimizations before achieving full general availability."
)

"""
Example usage:

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
    '''A class that is nearly final, but still in release-candidate stage.'''
    pass

@release_candidate("1.23.1-rc1")
class MyRCClass:
    '''A class that is nearly final, but still in release-candidate stage.'''
    pass
"""


def _update_docstring(obj: Callable | T, note: str) -> None:
    """Append or set the docstring of the given object with the specified note."""
    if obj.__doc__:
        obj.__doc__ += f"\n\n{note}"
    else:
        obj.__doc__ = note


def stage(
    status: str = "experimental",
    version: str | None = None,
    note: str | None = None,
) -> Callable[[Callable | T], Callable | T]:
    """A general-purpose decorator for marking a function or a class.

    It updates the docstring and attaches 'stage_status' (and optionally
    'stage_version') as metadata. A custom 'note' may be provided to
    override the default appended text.

    Args:
        status: The development stage (e.g., 'experimental', 'release_candidate', etc.).
        version: Optional version or release info (e.g., '1.21.0-rc4').
        note: A custom note to append to the docstring. If omitted, a default
              note is used to indicate the stage and possible changes.

    Returns:
        A decorator that updates the docstring and metadata of
        the target function/class.
    """

    def decorator(obj: Callable | T) -> Callable | T:
        entity_type = "class" if isinstance(obj, type) else "function"
        ver_text = f" (Version: {version})" if version else ""
        default_note = f"Note: This {entity_type} is marked as '{status}'{ver_text} and may change in the future."
        final_note = note if note else default_note

        _update_docstring(obj, final_note)
        setattr(obj, "stage_status", status)
        if version:
            setattr(obj, "stage_version", version)

        return obj

    return decorator


def experimental(obj: Callable | T) -> Callable | T:
    """Decorator specifically for 'experimental' features.

    It uses the general 'stage' decorator but also attaches
    'is_experimental = True'.
    """
    decorated = stage(status="experimental")(obj)
    setattr(decorated, "is_experimental", True)
    return decorated


def release_candidate(
    func: Callable | T | None = None,
    *,
    version: str | None = None,
    doc_string: str | None = None,
) -> Callable[[Callable | T], Callable | T] | Callable | T:
    """Decorator that designates a function/class as being in a 'release candidate' state.

    By default, applies a descriptive note indicating near-completion and possible minor refinements
    before achieving general availability. You may override this with a custom 'doc_string' if needed.

    Usage:
        1) @release_candidate
        2) @release_candidate()
        3) @release_candidate("1.21.3-rc1")
        4) @release_candidate(version="1.21.3-rc1")
        5) @release_candidate(doc_string="Custom RC note...")
        6) @release_candidate(version="1.21.3-rc1", doc_string="Custom RC note...")

    Args:
        func:
            - In cases (1) or (2), this is the function/class being decorated.
            - In cases (3) or (4), this may be a version string or None.
        version:
            The RC version string, if provided.
        doc_string:
            An optional custom note to append to the docstring, overriding
            the default RC descriptive note.

    Returns:
        The decorated object, with an updated docstring and
        'is_release_candidate = True'.
    """
    from semantic_kernel import DEFAULT_RC_VERSION

    def _apply(obj: Callable | T, ver: str, note: str | None) -> Callable | T:
        if note is not None:
            rc_note = note
        else:
            ver_text = f" (Version: {ver})" if ver else ""
            rc_note = f"{DEFAULT_RC_NOTE}{ver_text}"

        decorated = stage(status="release_candidate", version=ver, note=rc_note)(obj)
        setattr(decorated, "is_release_candidate", True)
        return decorated

    if callable(func):
        ver = version or DEFAULT_RC_VERSION
        return _apply(func, ver, doc_string)

    ver_str: str | None = func if isinstance(func, str) else version

    def wrapper(obj: Callable | T) -> Callable | T:
        return _apply(obj, ver_str or DEFAULT_RC_VERSION, doc_string)

    return wrapper
