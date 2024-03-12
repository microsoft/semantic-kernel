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
import sys
from typing import Callable, Dict

from google.cloud.pubsublite.internal.wait_ignore_cancelled import wait_ignore_cancelled
from google.cloud.pubsublite.internal.wire.partition_count_watcher import (
    PartitionCountWatcher,
)
from google.cloud.pubsublite.internal.wire.publisher import Publisher
from google.cloud.pubsublite.internal.wire.routing_policy import RoutingPolicy
from google.cloud.pubsublite.types import MessageMetadata, Partition
from google.cloud.pubsublite_v1 import PubSubMessage


class PartitionCountWatchingPublisher(Publisher):
    _publishers: Dict[Partition, Publisher]
    _publisher_factory: Callable[[Partition], Publisher]
    _policy_factory: Callable[[int], RoutingPolicy]
    _watcher: PartitionCountWatcher
    _partition_count_poller: asyncio.Future

    def __init__(
        self,
        watcher: PartitionCountWatcher,
        publisher_factory: Callable[[Partition], Publisher],
        policy_factory: Callable[[int], RoutingPolicy],
    ):
        self._publishers = {}
        self._publisher_factory = publisher_factory
        self._policy_factory = policy_factory
        self._watcher = watcher
        self._partition_count_poller = None

    async def __aenter__(self):
        try:
            await self._watcher.__aenter__()
            await self._poll_partition_count_action()
        except Exception:
            await self._watcher.__aexit__(*sys.exc_info())
            raise
        self._partition_count_poller = asyncio.ensure_future(
            self._watch_partition_count()
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._partition_count_poller is not None:
            self._partition_count_poller.cancel()
            await wait_ignore_cancelled(self._partition_count_poller)
            await self._watcher.__aexit__(exc_type, exc_val, exc_tb)
        for publisher in self._publishers.values():
            await publisher.__aexit__(exc_type, exc_val, exc_tb)

    async def _poll_partition_count_action(self):
        partition_count = await self._watcher.get_partition_count()
        await self._handle_partition_count_update(partition_count)

    async def _watch_partition_count(self):
        while True:
            await self._poll_partition_count_action()

    async def _handle_partition_count_update(self, partition_count: int):
        current_count = len(self._publishers)
        if current_count == partition_count:
            return
        if current_count > partition_count:
            return

        new_publishers = {
            Partition(index): self._publisher_factory(Partition(index))
            for index in range(current_count, partition_count)
        }
        await asyncio.gather(*[p.__aenter__() for p in new_publishers.values()])
        routing_policy = self._policy_factory(partition_count)

        self._publishers.update(new_publishers)
        self._routing_policy = routing_policy

    async def publish(self, message: PubSubMessage) -> MessageMetadata:
        partition = self._routing_policy.route(message)
        assert partition in self._publishers
        publisher = self._publishers[partition]
        return await publisher.publish(message)
