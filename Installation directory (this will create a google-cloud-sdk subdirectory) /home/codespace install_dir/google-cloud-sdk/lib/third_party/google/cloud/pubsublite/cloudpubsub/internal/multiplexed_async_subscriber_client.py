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

from typing import (
    Union,
    AsyncIterator,
    Awaitable,
    Callable,
    Optional,
    Set,
)

from google.cloud.pubsub_v1.subscriber.message import Message

from google.cloud.pubsublite.cloudpubsub.internal.single_subscriber import (
    AsyncSubscriberFactory,
    AsyncSingleSubscriber,
)
from google.cloud.pubsublite.cloudpubsub.subscriber_client_interface import (
    AsyncSubscriberClientInterface,
)
from google.cloud.pubsublite.types import (
    SubscriptionPath,
    FlowControlSettings,
    Partition,
)


async def _iterate_subscriber(
    subscriber: AsyncSingleSubscriber, on_failure: Callable[[], Awaitable[None]]
) -> AsyncIterator[Message]:
    try:
        while True:
            batch = await subscriber.read()
            for message in batch:
                yield message
    except:  # noqa: E722
        await on_failure()
        raise


class MultiplexedAsyncSubscriberClient(AsyncSubscriberClientInterface):
    _underlying_factory: AsyncSubscriberFactory
    _live_clients: Set[AsyncSingleSubscriber]

    def __init__(self, underlying_factory: AsyncSubscriberFactory):
        self._underlying_factory = underlying_factory
        self._live_clients = set()

    async def subscribe(
        self,
        subscription: Union[SubscriptionPath, str],
        per_partition_flow_control_settings: FlowControlSettings,
        fixed_partitions: Optional[Set[Partition]] = None,
    ) -> AsyncIterator[Message]:
        if isinstance(subscription, str):
            subscription = SubscriptionPath.parse(subscription)

        subscriber = self._underlying_factory(
            subscription, fixed_partitions, per_partition_flow_control_settings
        )
        await subscriber.__aenter__()
        self._live_clients.add(subscriber)

        return _iterate_subscriber(
            subscriber, lambda: self._try_remove_client(subscriber)
        )

    async def __aenter__(self):
        return self

    async def _try_remove_client(self, client: AsyncSingleSubscriber):
        if client in self._live_clients:
            self._live_clients.remove(client)
            await client.__aexit__(None, None, None)

    async def __aexit__(self, exc_type, exc_value, traceback):
        live_clients = self._live_clients
        self._live_clients = set()
        for client in live_clients:
            await client.__aexit__(None, None, None)
