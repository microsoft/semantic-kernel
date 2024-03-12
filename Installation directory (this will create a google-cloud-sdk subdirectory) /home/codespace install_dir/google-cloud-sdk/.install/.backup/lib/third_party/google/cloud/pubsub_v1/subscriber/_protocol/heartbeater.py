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

from __future__ import absolute_import

import logging
import threading
import typing
from typing import Optional

if typing.TYPE_CHECKING:  # pragma: NO COVER
    from google.cloud.pubsub_v1.subscriber._protocol.streaming_pull_manager import (
        StreamingPullManager,
    )


_LOGGER = logging.getLogger(__name__)
_HEARTBEAT_WORKER_NAME = "Thread-Heartbeater"
# How often to send heartbeats in seconds. Determined as half the period of
# time where the Pub/Sub server will close the stream as inactive, which is
# 60 seconds.
_DEFAULT_PERIOD = 30


class Heartbeater(object):
    def __init__(self, manager: "StreamingPullManager", period: int = _DEFAULT_PERIOD):
        self._thread: Optional[threading.Thread] = None
        self._operational_lock = threading.Lock()
        self._manager = manager
        self._stop_event = threading.Event()
        self._period = period

    def heartbeat(self) -> None:
        """Periodically send streaming pull heartbeats."""
        while not self._stop_event.is_set():
            if self._manager.heartbeat():
                _LOGGER.debug("Sent heartbeat.")
            self._stop_event.wait(timeout=self._period)

        _LOGGER.debug("%s exiting.", _HEARTBEAT_WORKER_NAME)

    def start(self) -> None:
        with self._operational_lock:
            if self._thread is not None:
                raise ValueError("Heartbeater is already running.")

            # Create and start the helper thread.
            self._stop_event.clear()
            thread = threading.Thread(
                name=_HEARTBEAT_WORKER_NAME, target=self.heartbeat
            )
            thread.daemon = True
            thread.start()
            _LOGGER.debug("Started helper thread %s", thread.name)
            self._thread = thread

    def stop(self) -> None:
        with self._operational_lock:
            self._stop_event.set()

            if self._thread is not None:
                # The thread should automatically exit when the consumer is
                # inactive.
                self._thread.join()

            self._thread = None
