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

from concurrent.futures.thread import ThreadPoolExecutor
from typing import Union, Optional, Set
from threading import Lock

from google.cloud.pubsub_v1.subscriber.futures import StreamingPullFuture

from google.cloud.pubsublite.cloudpubsub.internal.single_subscriber import (
    AsyncSubscriberFactory,
)
from google.cloud.pubsublite.cloudpubsub.internal.subscriber_impl import SubscriberImpl
from google.cloud.pubsublite.cloudpubsub.subscriber_client_interface import (
    SubscriberClientInterface,
    MessageCallback,
)
from google.cloud.pubsublite.types import (
    SubscriptionPath,
    FlowControlSettings,
    Partition,
)


class MultiplexedSubscriberClient(SubscriberClientInterface):
    _executor: ThreadPoolExecutor
    _underlying_factory: AsyncSubscriberFactory

    _lock: Lock
    _live_clients: Set[StreamingPullFuture]

    def __init__(
        self, executor: ThreadPoolExecutor, underlying_factory: AsyncSubscriberFactory
    ):
        self._executor = executor
        self._underlying_factory = underlying_factory
        self._lock = Lock()
        self._live_clients = set()

    def subscribe(
        self,
        subscription: Union[SubscriptionPath, str],
        callback: MessageCallback,
        per_partition_flow_control_settings: FlowControlSettings,
        fixed_partitions: Optional[Set[Partition]] = None,
    ) -> StreamingPullFuture:
        if isinstance(subscription, str):
            subscription = SubscriptionPath.parse(subscription)

        underlying = self._underlying_factory(
            subscription, fixed_partitions, per_partition_flow_control_settings
        )
        subscriber = SubscriberImpl(underlying, callback, self._executor)
        future = StreamingPullFuture(subscriber)
        subscriber.__enter__()
        future.add_done_callback(lambda fut: self._try_remove_client(future))
        return future

    @staticmethod
    def _cancel_streaming_pull_future(fut: StreamingPullFuture):
        try:
            fut.cancel()
            fut.result()
        except:  # noqa: E722
            pass

    def _try_remove_client(self, future: StreamingPullFuture):
        with self._lock:
            if future not in self._live_clients:
                return
            self._live_clients.remove(future)
        self._cancel_streaming_pull_future(future)

    def __enter__(self):
        self._executor.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        with self._lock:
            live_clients = self._live_clients
            self._live_clients = set()
        for client in live_clients:
            self._cancel_streaming_pull_future(client)
        self._executor.__exit__(exc_type, exc_value, traceback)
