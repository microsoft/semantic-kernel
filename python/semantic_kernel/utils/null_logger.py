# Copyright (c) Microsoft. All rights reserved.

from logging import Logger


class NullLogger(Logger):
    """
    A logger that does nothing.
    """

    def __init__(self) -> None:
        pass

    def debug(self, _: str) -> None:
        pass

    def info(self, _: str) -> None:
        pass

    def warning(self, _: str) -> None:
        pass

    def error(self, _: str) -> None:
        pass
