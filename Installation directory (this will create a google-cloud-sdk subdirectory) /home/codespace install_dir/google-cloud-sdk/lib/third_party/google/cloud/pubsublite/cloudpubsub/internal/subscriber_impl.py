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

import concurrent.futures
import threading
from concurrent.futures.thread import ThreadPoolExecutor
from typing import ContextManager, Optional
from google.api_core.exceptions import GoogleAPICallError
from functools import partial

from google.cloud.pubsublite.internal.wait_ignore_cancelled import wait_ignore_errors
from google.cloud.pubsublite.cloudpubsub.internal.managed_event_loop import (
    ManagedEventLoop,
)
from google.cloud.pubsublite.cloudpubsub.internal.streaming_pull_manager import (
    StreamingPullManager,
    CloseCallback,
)
from google.cloud.pubsublite.cloudpubsub.internal.single_subscriber import (
    AsyncSingleSubscriber,
)
from google.cloud.pubsublite.cloudpubsub.subscriber_client_interface import (
    MessageCallback,
)


class SubscriberImpl(ContextManager, StreamingPullManager):
    _underlying: AsyncSingleSubscriber
    _callback: MessageCallback
    _unowned_executor: ThreadPoolExecutor

    _event_loop: ManagedEventLoop

    _poller_future: concurrent.futures.Future
    _close_lock: threading.Lock
    _failure: Optional[GoogleAPICallError]
    _close_callback: Optional[CloseCallback]
    _closed: bool

    def __init__(
        self,
        underlying: AsyncSingleSubscriber,
        callback: MessageCallback,
        unowned_executor: ThreadPoolExecutor,
    ):
        self._underlying = underlying
        self._callback = callback
        self._unowned_executor = unowned_executor
        self._event_loop = ManagedEventLoop("SubscriberLoopThread")
        self._close_lock = threading.Lock()
        self._failure = None
        self._close_callback = None
        self._closed = False

    def add_close_callback(self, close_callback: CloseCallback):
        """
        A close callback must be set exactly once by the StreamingPullFuture managing this subscriber.

        This two-phase init model is made necessary by the requirements of StreamingPullFuture.
        """
        with self._close_lock:
            assert self._close_callback is None
            self._close_callback = close_callback

    def close(self):
        with self._close_lock:
            if self._closed:
                return
            self._closed = True
        self.__exit__(None, None, None)

    def _fail(self, error: GoogleAPICallError):
        self._failure = error
        self.close()

    async def _poller(self):
        try:
            while True:
                batch = await self._underlying.read()
                self._unowned_executor.map(self._callback, batch)
        except GoogleAPICallError as e:
            self._unowned_executor.submit(partial(self._fail, e))

    def __enter__(self):
        assert self._close_callback is not None
        self._event_loop.__enter__()
        self._event_loop.submit(self._underlying.__aenter__()).result()
        self._poller_future = self._event_loop.submit(self._poller())
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._poller_future.cancel()
        try:
            self._poller_future.result()  # Ignore error.
        except:  # noqa: E722
            pass
        self._event_loop.submit(
            wait_ignore_errors(
                self._underlying.__aexit__(exc_type, exc_value, traceback)
            )
        ).result()
        self._event_loop.__exit__(exc_type, exc_value, traceback)
        assert self._close_callback is not None
        self._close_callback(self, self._failure)
