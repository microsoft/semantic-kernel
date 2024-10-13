# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream


class NullLogger(Logger):
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
>>>>>>> head


class NullLogger(Logger):
from functools import wraps
from logging import Logger, getLogger
from typing import Any, Callable
>>>>>>> origin/main

logger: Logger = getLogger(__name__)

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
# TODO: delete
=======
logger: Logger = getLogger(__name__)

# TODO: delete

<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main

=======
# TODO: delete

>>>>>>> Stashed changes
=======
# TODO: delete
>>>>>>> head

>>>>>>> Stashed changes

<<<<<<< main
class NullLogger(Logger):
=======
def _nullify(fn) -> Callable[[Any], None]:
    """General wrapper to not call wrapped function"""

    @wraps(fn)
    def _inner_nullify(*args, **kwargs) -> None:
        return

    return _inner_nullify


class _NullerMeta(type):
    def __new__(cls, classname, base_classes, class_dict):
        """Return a Class that nullifies all Logger object callbacks"""
        nullified_dict = {attr_name: _nullify(attr) for attr_name, attr in Logger.__dict__.items() if callable(attr)}
        return type.__new__(cls, classname, base_classes, {**class_dict, **nullified_dict})


class NullLogger(Logger, metaclass=_NullerMeta):
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    """
    A logger that does nothing.
    """

    def __init__(self) -> None:
        pass

    def debug(self, _: str) -> None:
        pass

    def info(self, _: str) -> None:
        pass
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
>>>>>>> head

    def warning(self, _: str) -> None:
        pass

    def error(self, _: str) -> None:
        pass
    def __init__(self):
        super().__init__(None)
        logger.warning(
            (
                "NullLogger is deprecated and will be removed in a future release,",
                "the same goes for all 'log' and 'logger' arguments.",
            )
        )
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head

    def warning(self, _: str) -> None:
        pass

    def error(self, _: str) -> None:
        pass
