# Copyright (c) Microsoft. All rights reserved.


from collections.abc import AsyncIterable, Sequence
from typing import TypeVar

_T = TypeVar("_T")


async def desync_list(sync_list: Sequence[_T]) -> AsyncIterable[_T]:  # noqa: RUF029
    """De synchronize a list of synchronous objects."""
    for x in sync_list:
        yield x
