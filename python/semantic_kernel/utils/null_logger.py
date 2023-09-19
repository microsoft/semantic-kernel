# Copyright (c) Microsoft. All rights reserved.

from functools import wraps
from logging import Logger
from typing import Any, Callable


def _nullify(fn) -> Callable[[Any], None]:
    """General wrapper to not call wrapped function"""

    @wraps(fn)
    def _inner_nullify(*args, **kwargs) -> None:
        return

    return _inner_nullify


class _NullerMeta(type):
    def __new__(cls, classname, base_classes, class_dict):
        """Return a Class that nullifies all Logger object callbacks"""
        nullified_dict = {
            attr_name: _nullify(attr)
            for attr_name, attr in Logger.__dict__.items()
            if callable(attr)
        }
        return type.__new__(
            cls, classname, base_classes, {**class_dict, **nullified_dict}
        )


class NullLogger(Logger, metaclass=_NullerMeta):
    """
    A logger that does nothing.
    """

    def __init__(self):
        super().__init__(None)
