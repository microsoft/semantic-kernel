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

from concurrent.futures import Future
from typing import Mapping

from google.cloud.pubsublite.cloudpubsub.internal.managed_event_loop import (
    ManagedEventLoop,
)
from google.cloud.pubsublite.cloudpubsub.internal.single_publisher import (
    SinglePublisher,
    AsyncSinglePublisher,
)


class SinglePublisherImpl(SinglePublisher):
    _managed_loop: ManagedEventLoop
    _underlying: AsyncSinglePublisher

    def __init__(self, underlying: AsyncSinglePublisher):
        super().__init__()
        self._managed_loop = ManagedEventLoop("PublisherLoopThread")
        self._underlying = underlying

    def publish(
        self, data: bytes, ordering_key: str = "", **attrs: Mapping[str, str]
    ) -> "Future[str]":
        return self._managed_loop.submit(
            self._underlying.publish(data=data, ordering_key=ordering_key, **attrs)
        )

    def __enter__(self):
        self._managed_loop.__enter__()
        self._managed_loop.submit(self._underlying.__aenter__()).result()
        return self

    def __exit__(self, __exc_type, __exc_value, __traceback):
        self._managed_loop.submit(
            self._underlying.__aexit__(__exc_type, __exc_value, __traceback)
        ).result()
        self._managed_loop.__exit__(__exc_type, __exc_value, __traceback)
