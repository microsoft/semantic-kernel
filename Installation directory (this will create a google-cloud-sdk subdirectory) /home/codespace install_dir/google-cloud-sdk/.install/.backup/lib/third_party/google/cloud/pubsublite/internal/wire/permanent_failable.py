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
from typing import Awaitable, TypeVar, Optional, Callable

from google.api_core.exceptions import GoogleAPICallError, Unknown

from google.cloud.pubsublite.internal.wait_ignore_cancelled import wait_ignore_errors

T = TypeVar("T")


def adapt_error(e: Exception) -> GoogleAPICallError:
    if isinstance(e, GoogleAPICallError):
        return e
    return Unknown("Had an unknown error", errors=[e])


class _TaskWithCleanup:
    def __init__(self, a: Awaitable):
        self._task = asyncio.ensure_future(a)

    async def __aenter__(self):
        return self._task

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if not self._task.done():
            self._task.cancel()
            await wait_ignore_errors(self._task)


class PermanentFailable:
    """A class that can experience permanent failures, with helpers for forwarding these to client actions."""

    _maybe_failure_task: Optional[asyncio.Future]

    def __init__(self):
        self._maybe_failure_task = None

    @property
    def _failure_task(self) -> asyncio.Future:
        """Get the failure task, initializing it lazily, since it needs to be initialized in the event loop."""
        if self._maybe_failure_task is None:
            self._maybe_failure_task = asyncio.Future()
        return self._maybe_failure_task

    async def await_unless_failed(self, awaitable: Awaitable[T]) -> T:
        """
        Await the awaitable, unless fail() is called first.
        Args:
          awaitable: An awaitable

        Returns: The result of the awaitable
        Raises: The permanent error if fail() is called or the awaitable raises one.
        """
        async with _TaskWithCleanup(awaitable) as task:
            if self._failure_task.done():
                raise self._failure_task.exception()
            done, _ = await asyncio.wait(
                [task, self._failure_task], return_when=asyncio.FIRST_COMPLETED
            )
            if task in done:
                return await task
            raise self._failure_task.exception()

    async def run_poller(self, poll_action: Callable[[], Awaitable[None]]):
        """
        Run a polling loop, which runs poll_action forever unless this is failed.
        Args:
          poll_action: A callable returning an awaitable to run in a loop. Note that async functions which return once
          satisfy this.
        """
        try:
            while True:
                await self.await_unless_failed(poll_action())
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.fail(adapt_error(e))

    def fail(self, err: GoogleAPICallError):
        if not self._failure_task.done():
            self._failure_task.set_exception(err)
            # Ensure that even if _failure_task is never used, the exception is
            # retrieved and the asyncio runtime doesn't print an error.
            self._failure_task.exception()

    def error(self) -> Optional[GoogleAPICallError]:
        if not self._failure_task.done():
            return None
        return self._failure_task.exception()
