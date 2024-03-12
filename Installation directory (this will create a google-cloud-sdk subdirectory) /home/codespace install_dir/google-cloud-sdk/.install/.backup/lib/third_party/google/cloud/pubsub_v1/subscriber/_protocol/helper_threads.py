# Copyright 2017, Google LLC All rights reserved.
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

import logging
import queue
import time
from typing import Any, Callable, List, Sequence
import uuid


__all__ = ("QueueCallbackWorker", "STOP")

_LOGGER = logging.getLogger(__name__)


# Helper thread stop indicator. This could be a sentinel object or None,
# but the sentinel object's ID can change if the process is forked, and
# None has the possibility of a user accidentally killing the helper
# thread.
STOP = uuid.uuid4()


def _get_many(
    queue_: queue.Queue, max_items: int = None, max_latency: float = 0
) -> List[Any]:
    """Get multiple items from a Queue.

    Gets at least one (blocking) and at most ``max_items`` items
    (non-blocking) from a given Queue. Does not mark the items as done.

    Args:
        queue_: The Queue to get items from.
        max_items:
            The maximum number of items to get. If ``None``, then all available items
            in the queue are returned.
        max_latency:
            The maximum number of seconds to wait for more than one item from a queue.
            This number includes the time required to retrieve the first item.

    Returns:
        A sequence of items retrieved from the queue.
    """
    start = time.time()
    # Always return at least one item.
    items = [queue_.get()]
    while max_items is None or len(items) < max_items:
        try:
            elapsed = time.time() - start
            timeout = max(0, max_latency - elapsed)
            items.append(queue_.get(timeout=timeout))
        except queue.Empty:
            break
    return items


class QueueCallbackWorker(object):
    """A helper that executes a callback for items sent in a queue.

    Calls a blocking ``get()`` on the ``queue`` until it encounters
    :attr:`STOP`.

    Args:
        queue:
            A Queue instance, appropriate for crossing the concurrency boundary
            implemented by ``executor``. Items will be popped off (with a blocking
            ``get()``) until :attr:`STOP` is encountered.
        callback:
            A callback that can process items pulled off of the queue. Multiple items
            will be passed to the callback in batches.
        max_items:
            The maximum amount of items that will be passed to the callback at a time.
        max_latency:
            The maximum amount of time in seconds to wait for additional items before
            executing the callback.
    """

    def __init__(
        self,
        queue: queue.Queue,
        callback: Callable[[Sequence[Any]], Any],
        max_items: int = 100,
        max_latency: float = 0,
    ):
        self.queue = queue
        self._callback = callback
        self.max_items = max_items
        self.max_latency = max_latency

    def __call__(self) -> None:
        continue_ = True
        while continue_:
            items = _get_many(
                self.queue, max_items=self.max_items, max_latency=self.max_latency
            )

            # If stop is in the items, process all items up to STOP and then
            # exit.
            try:
                items = items[: items.index(STOP)]
                continue_ = False
            except ValueError:
                pass

            # Run the callback. If any exceptions occur, log them and
            # continue.
            try:
                self._callback(items)
            except Exception as exc:
                _LOGGER.exception("Error in queue callback worker: %s", exc)

        _LOGGER.debug("Exiting the QueueCallbackWorker.")
