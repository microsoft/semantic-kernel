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
from typing import Mapping

from google.cloud.pubsublite.internal.wire.publisher import Publisher
from google.cloud.pubsublite.internal.wire.routing_policy import RoutingPolicy
from google.cloud.pubsublite.types import Partition, MessageMetadata
from google.cloud.pubsublite_v1 import PubSubMessage


class RoutingPublisher(Publisher):
    _routing_policy: RoutingPolicy
    _publishers: Mapping[Partition, Publisher]

    def __init__(
        self, routing_policy: RoutingPolicy, publishers: Mapping[Partition, Publisher]
    ):
        self._routing_policy = routing_policy
        self._publishers = publishers

    async def __aenter__(self):
        enter_futures = [
            publisher.__aenter__() for publisher in self._publishers.values()
        ]
        await asyncio.gather(*enter_futures)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        for publisher in self._publishers.values():
            await publisher.__aexit__(exc_type, exc_val, exc_tb)

    async def publish(self, message: PubSubMessage) -> MessageMetadata:
        partition = self._routing_policy.route(message)
        assert partition in self._publishers
        return await self._publishers[partition].publish(message)
