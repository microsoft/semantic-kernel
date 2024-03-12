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

from typing import Callable, Union, Mapping

from google.api_core.exceptions import GoogleAPICallError

from google.cloud.pubsublite.cloudpubsub.internal.client_multiplexer import (
    AsyncClientMultiplexer,
)
from google.cloud.pubsublite.cloudpubsub.internal.single_publisher import (
    AsyncSinglePublisher,
)
from google.cloud.pubsublite.cloudpubsub.publisher_client_interface import (
    AsyncPublisherClientInterface,
)
from google.cloud.pubsublite.types import TopicPath


AsyncPublisherFactory = Callable[[TopicPath], AsyncSinglePublisher]


class MultiplexedAsyncPublisherClient(AsyncPublisherClientInterface):
    _publisher_factory: AsyncPublisherFactory
    _multiplexer: AsyncClientMultiplexer[TopicPath, AsyncSinglePublisher]

    def __init__(self, publisher_factory: AsyncPublisherFactory):
        self._publisher_factory = publisher_factory
        self._multiplexer = AsyncClientMultiplexer(
            lambda topic: self._create_and_open(topic)
        )

    async def _create_and_open(self, topic: TopicPath):
        client = self._publisher_factory(topic)
        await client.__aenter__()
        return client

    async def publish(
        self,
        topic: Union[TopicPath, str],
        data: bytes,
        ordering_key: str = "",
        **attrs: Mapping[str, str]
    ) -> str:
        if isinstance(topic, str):
            topic = TopicPath.parse(topic)

        publisher = await self._multiplexer.get_or_create(topic)
        try:
            return await publisher.publish(
                data=data, ordering_key=ordering_key, **attrs
            )
        except GoogleAPICallError as e:
            await self._multiplexer.try_erase(topic, publisher)
            raise e

    async def __aenter__(self):
        await self._multiplexer.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self._multiplexer.__aexit__(exc_type, exc_value, traceback)
