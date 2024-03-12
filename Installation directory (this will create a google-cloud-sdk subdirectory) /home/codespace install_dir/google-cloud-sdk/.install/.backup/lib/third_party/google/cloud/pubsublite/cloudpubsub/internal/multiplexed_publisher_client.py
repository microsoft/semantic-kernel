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
from typing import Callable, Union, Mapping

from google.api_core.exceptions import GoogleAPICallError

from google.cloud.pubsublite.cloudpubsub.internal.client_multiplexer import (
    ClientMultiplexer,
)
from google.cloud.pubsublite.cloudpubsub.internal.single_publisher import (
    SinglePublisher,
)
from google.cloud.pubsublite.cloudpubsub.publisher_client_interface import (
    PublisherClientInterface,
)
from google.cloud.pubsublite.types import TopicPath

PublisherFactory = Callable[[TopicPath], SinglePublisher]


class MultiplexedPublisherClient(PublisherClientInterface):
    _publisher_factory: PublisherFactory
    _multiplexer: ClientMultiplexer[TopicPath, SinglePublisher]

    def __init__(self, publisher_factory: PublisherFactory):
        self._publisher_factory = publisher_factory
        self._multiplexer = ClientMultiplexer(
            lambda topic: self._create_and_start_publisher(topic)
        )

    def publish(
        self,
        topic: Union[TopicPath, str],
        data: bytes,
        ordering_key: str = "",
        **attrs: Mapping[str, str]
    ) -> "Future[str]":
        if isinstance(topic, str):
            topic = TopicPath.parse(topic)
        try:
            publisher = self._multiplexer.get_or_create(topic)
        except GoogleAPICallError as e:
            failed = Future()
            failed.set_exception(e)
            return failed
        future = publisher.publish(data=data, ordering_key=ordering_key, **attrs)
        future.add_done_callback(
            lambda fut: self._on_future_completion(topic, publisher, fut)
        )
        return future

    def _create_and_start_publisher(self, topic: Union[TopicPath, str]):
        publisher = self._publisher_factory(topic)
        try:
            return publisher.__enter__()
        except GoogleAPICallError:
            publisher.__exit__(None, None, None)
            raise

    def _on_future_completion(
        self, topic: TopicPath, publisher: SinglePublisher, future: "Future[str]"
    ):
        try:
            future.result()
        except GoogleAPICallError:
            self._multiplexer.try_erase(topic, publisher)

    def __enter__(self):
        self._multiplexer.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._multiplexer.__exit__(exc_type, exc_value, traceback)
