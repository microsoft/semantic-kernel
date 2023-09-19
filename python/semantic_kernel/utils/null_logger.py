# Copyright (c) Microsoft. All rights reserved.

from functools import wraps
from logging import Logger


def _nullify(fn):
    @wraps(fn)
    def _inner_nullify(*args, **kwargs):
        pass

    return _inner_nullify


class _NullerMeta(type):
    def __new__(cls, classname, base_classes, class_dict):
        nullified_dict = {
            attr_name: _nullify(attr)
            for attr_name, attr in class_dict.items()
            if callable(attr)
        }
        return type.__new__(
            cls, classname, base_classes, {**class_dict, **nullified_dict}
        )


class NullLogger(Logger):
    """
    A logger that does nothing.
    """

    __metaclass__ = _NullerMeta
