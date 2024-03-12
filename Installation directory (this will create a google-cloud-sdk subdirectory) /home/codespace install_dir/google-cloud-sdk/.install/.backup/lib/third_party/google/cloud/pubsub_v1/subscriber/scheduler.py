# Copyright 2018, Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Schedulers provide means to *schedule* callbacks asynchronously.

These are used by the subscriber to call the user-provided callback to process
each message.
"""

import abc
import concurrent.futures
import queue
import typing
from typing import Callable, List, Optional
import warnings

if typing.TYPE_CHECKING:  # pragma: NO COVER
    from google.cloud import pubsub_v1


class Scheduler(metaclass=abc.ABCMeta):
    """Abstract base class for schedulers.

    Schedulers are used to schedule callbacks asynchronously.
    """

    @property
    @abc.abstractmethod
    def queue(self) -> queue.Queue:  # pragma: NO COVER
        """Queue: A concurrency-safe queue specific to the underlying
        concurrency implementation.

        This queue is used to send messages *back* to the scheduling actor.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def schedule(self, callback: Callable, *args, **kwargs) -> None:  # pragma: NO COVER
        """Schedule the callback to be called asynchronously.

        Args:
            callback: The function to call.
            args: Positional arguments passed to the callback.
            kwargs: Key-word arguments passed to the callback.

        Returns:
            None
        """
        raise NotImplementedError

    @abc.abstractmethod
    def shutdown(
        self, await_msg_callbacks: bool = False
    ) -> List["pubsub_v1.subscriber.message.Message"]:  # pragma: NO COVER
        """Shuts down the scheduler and immediately end all pending callbacks.

        Args:
            await_msg_callbacks:
                If ``True``, the method will block until all currently executing
                callbacks are done processing. If ``False`` (default), the
                method will not wait for the currently running callbacks to complete.

        Returns:
            The messages submitted to the scheduler that were not yet dispatched
            to their callbacks.
            It is assumed that each message was submitted to the scheduler as the
            first positional argument to the provided callback.
        """
        raise NotImplementedError


def _make_default_thread_pool_executor() -> concurrent.futures.ThreadPoolExecutor:
    return concurrent.futures.ThreadPoolExecutor(
        max_workers=10, thread_name_prefix="ThreadPoolExecutor-ThreadScheduler"
    )


class ThreadScheduler(Scheduler):
    """A thread pool-based scheduler. It must not be shared across
       SubscriberClients.

    This scheduler is useful in typical I/O-bound message processing.

    Args:
        executor:
            An optional executor to use. If not specified, a default one
            will be created.
    """

    def __init__(
        self, executor: Optional[concurrent.futures.ThreadPoolExecutor] = None
    ):
        self._queue: queue.Queue = queue.Queue()
        if executor is None:
            self._executor = _make_default_thread_pool_executor()
        else:
            self._executor = executor

    @property
    def queue(self):
        """Queue: A thread-safe queue used for communication between callbacks
        and the scheduling thread."""
        return self._queue

    def schedule(self, callback: Callable, *args, **kwargs) -> None:
        """Schedule the callback to be called asynchronously in a thread pool.

        Args:
            callback: The function to call.
            args: Positional arguments passed to the callback.
            kwargs: Key-word arguments passed to the callback.

        Returns:
            None
        """
        try:
            self._executor.submit(callback, *args, **kwargs)
        except RuntimeError:
            warnings.warn(
                "Scheduling a callback after executor shutdown.",
                category=RuntimeWarning,
                stacklevel=2,
            )

    def shutdown(
        self, await_msg_callbacks: bool = False
    ) -> List["pubsub_v1.subscriber.message.Message"]:
        """Shut down the scheduler and immediately end all pending callbacks.

        Args:
            await_msg_callbacks:
                If ``True``, the method will block until all currently executing
                executor threads are done processing. If ``False`` (default), the
                method will not wait for the currently running threads to complete.

        Returns:
            The messages submitted to the scheduler that were not yet dispatched
            to their callbacks.
            It is assumed that each message was submitted to the scheduler as the
            first positional argument to the provided callback.
        """
        dropped_messages = []

        # Drop all pending item from the executor. Without this, the executor will also
        # try to process any pending work items before termination, which is undesirable.
        #
        # TODO: Replace the logic below by passing `cancel_futures=True` to shutdown()
        # once we only need to support Python 3.9+.
        try:
            while True:
                work_item = self._executor._work_queue.get(block=False)
                if work_item is None:  # Exceutor in shutdown mode.
                    continue
                dropped_messages.append(work_item.args[0])
        except queue.Empty:
            pass

        self._executor.shutdown(wait=await_msg_callbacks)
        return dropped_messages
