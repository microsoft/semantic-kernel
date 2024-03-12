# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import threading
from typing import List, Union, Any, TypeVar, Generic, Optional, Callable, Awaitable

from unittest.mock import AsyncMock

T = TypeVar("T")


async def async_iterable(elts: List[Union[Any, Exception]]):
    for elt in elts:
        if isinstance(elt, Exception):
            raise elt
        yield elt


def make_queue_waiter(
    started_q: "asyncio.Queue[None]", result_q: "asyncio.Queue[Union[T, Exception]]"
) -> Callable[[], Awaitable[T]]:
    """
    Given a queue to notify when started and a queue to get results from, return a waiter which
    notifies started_q when started and returns from result_q when done.
    """

    async def waiter(*args, **kwargs):
        await started_q.put(None)
        result = await result_q.get()
        if isinstance(result, Exception):
            raise result
        return result

    return waiter


class QueuePair:
    called: asyncio.Queue
    results: asyncio.Queue

    def __init__(self):
        self.called = asyncio.Queue()
        self.results = asyncio.Queue()


def wire_queues(mock: AsyncMock) -> QueuePair:
    queues = QueuePair()
    mock.side_effect = make_queue_waiter(queues.called, queues.results)
    return queues


class Box(Generic[T]):
    val: Optional[T]


def run_on_thread(func: Callable[[], T]) -> T:
    box = Box()

    def set_box():
        box.val = func()

    # Initialize watcher on another thread with a different event loop.
    thread = threading.Thread(target=set_box)
    thread.start()
    thread.join()
    return box.val
