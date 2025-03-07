# Copyright (c) Microsoft. All rights reserved.

import asyncio
from collections.abc import Callable
from functools import partial
from typing import Any


async def run_in_executor(executor: Any, func: Callable, *args, **kwargs) -> Any:
    """Run a function in an executor."""
    return await asyncio.get_event_loop().run_in_executor(executor, partial(func, *args, **kwargs))
