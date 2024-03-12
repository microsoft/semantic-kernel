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
import logging
from concurrent.futures.thread import ThreadPoolExecutor
import asyncio

from google.cloud.pubsublite import AdminClientInterface
from google.cloud.pubsublite.internal.wait_ignore_cancelled import wait_ignore_cancelled
from google.cloud.pubsublite.internal.wire.partition_count_watcher import (
    PartitionCountWatcher,
)
from google.cloud.pubsublite.internal.wire.permanent_failable import PermanentFailable
from google.cloud.pubsublite.types import TopicPath
from google.api_core.exceptions import GoogleAPICallError


class PartitionCountWatcherImpl(PartitionCountWatcher, PermanentFailable):
    _admin: AdminClientInterface
    _topic_path: TopicPath
    _duration: float
    _any_success: bool
    _thread: ThreadPoolExecutor
    _queue: asyncio.Queue
    _partition_loop_poller: asyncio.Future

    def __init__(
        self, admin: AdminClientInterface, topic_path: TopicPath, duration: float
    ):
        super().__init__()
        self._admin = admin
        self._topic_path = topic_path
        self._duration = duration
        self._any_success = False

    async def __aenter__(self):
        self._thread = ThreadPoolExecutor(max_workers=1)
        self._queue = asyncio.Queue(maxsize=1)
        self._partition_loop_poller = asyncio.ensure_future(
            self.run_poller(self._poll_partition_loop)
        )

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._partition_loop_poller.cancel()
        await wait_ignore_cancelled(self._partition_loop_poller)
        self._thread.shutdown(wait=False)

    def _get_partition_count_sync(self) -> int:
        return self._admin.get_topic_partition_count(self._topic_path)

    async def _poll_partition_loop(self):
        try:
            partition_count = await asyncio.get_event_loop().run_in_executor(
                self._thread, self._get_partition_count_sync
            )
            self._any_success = True
            await self._queue.put(partition_count)
        except GoogleAPICallError as e:
            if not self._any_success:
                raise e
            logging.exception("Failed to retrieve partition count")
        await asyncio.sleep(self._duration)

    async def get_partition_count(self) -> int:
        return await self.await_unless_failed(self._queue.get())
