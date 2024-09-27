# Copyright (c) Microsoft. All rights reserved.

import asyncio
from functools import partial


async def run_in_executor(executor, func, *args, **kwargs):
    """Run a function in an executor."""
    return await asyncio.get_event_loop().run_in_executor(executor, partial(func, *args, **kwargs))


def remove_none_recursively(data: dict, max_depth: int = 5) -> dict:
    """Remove None values from a dictionary recursively."""
    if max_depth <= 0:
        return data

    if not isinstance(data, dict):
        return data

    return {k: remove_none_recursively(v, max_depth=max_depth - 1) for k, v in data.items() if v is not None}
